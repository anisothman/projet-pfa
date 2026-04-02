"""
Module pour normaliser et structurer les réponses Gemini en JSON standardisé

Ce module fournit:
- ResponseFormatter: Classe pour parser les réponses texte de Gemini et les structurer
- Validation des schémas JSON
- Conversion de markdown en structure JSON
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from logger_config import logger


class Impact(str, Enum):
    """Énumération des niveaux d'impact"""
    CRITIQUE = "critique"
    MAJEUR = "majeur"
    MODERE = "modéré"
    FAIBLE = "faible"


class Priorite(str, Enum):
    """Énumération des niveaux de priorité"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Severite(str, Enum):
    """Énumération des niveaux de sévérité"""
    CRITIQUE = "critique"
    MAJEUR = "majeur"
    MODERE = "modéré"
    FAIBLE = "faible"


@dataclass
class PointDiagnostic:
    """Représentation d'un point dans le diagnostic"""
    titre: str
    description: str
    impact: str = Impact.MODERE
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ActionPlan:
    """Représentation d'une action dans le plan"""
    action: str
    description: str
    priorite: str = Priorite.P1
    responsable: Optional[str] = None
    delai_jours: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


class ResponseFormatter:
    """
    Classe pour normaliser les réponses texte de Gemini en JSON structuré
    
    Utilisage:
        formatter = ResponseFormatter(company_name="Apple")
        response_text = gemini_client.generate_text(prompt)
        structured_json = formatter.format_diagnostic_response(response_text)
    """
    
    def __init__(self, company_name: str, model: str = "gemini-2.0-flash", 
                 version_prompt: str = "2.1", prompt_type: str = "diagnostic"):
        """
        Initialise le formateur
        
        Args:
            company_name: Nom de l'entreprise
            model: Modèle Gemini utilisé
            version_prompt: Version du prompt
            prompt_type: Type de prompt ("diagnostic" ou "plan_action")
        """
        self.company_name = company_name
        self.model = model
        self.version_prompt = version_prompt
        self.prompt_type = prompt_type
        self.start_time = datetime.now()
    
    def format_diagnostic_response(self, 
                                  response_text: str,
                                  company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse une réponse de diagnostic Gemini en JSON structuré
        
        Args:
            response_text: Réponse texte de Gemini
            company_data: Données de l'entreprise (provenant de SerpAPI)
            
        Returns:
            Dict contenant la structure complète du diagnostic
        """
        logger.info(f"Formatage de la réponse diagnostic pour {self.company_name}")
        
        # Parser la réponse
        points_forts = self._extract_section(response_text, r"points?\s+forts?", Impact.MAJEUR)
        points_faibles = self._extract_section(response_text, r"points?\s+faibles?", Impact.MAJEUR)
        opportunites = self._extract_section(response_text, r"opportunit[éè]es?", Impact.MAJEUR)
        
        # Analyser les avis si disponibles
        analyse_avis = self._analyze_reviews(response_text)
        
        # Construire la structure finale
        result = {
            "entreprise": self._normalize_company_data(company_data),
            "diagnostic": {
                "points_forts": points_forts,
                "points_faibles": points_faibles,
                "opportunites": opportunites
            },
            "analyse_avis": analyse_avis,
            "metadonnees": self._create_metadata()
        }
        
        logger.info("Diagnostic structuré avec succès")
        return result
    
    def format_plan_action_response(self, 
                                   response_text: str,
                                   company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse une réponse de plan d'action Gemini en JSON structuré
        
        Args:
            response_text: Réponse texte de Gemini
            company_data: Données de l'entreprise
            
        Returns:
            Dict contenant le plan d'action structuré
        """
        logger.info(f"Formatage du plan d'action pour {self.company_name}")
        
        # Parser les sections temporelles
        court_terme = self._extract_actions(response_text, r"court\s+terme\s*\(0-3\s+mois?\)", 90)
        moyen_terme = self._extract_actions(response_text, r"moyen\s+terme\s*\(3-6\s+mois?\)", 180)
        long_terme = self._extract_actions(response_text, r"long\s+terme\s*\(6-12\s+mois?\)", 365)
        
        # Extraire les KPIs et risques
        kpis = self._extract_kpis(response_text)
        risques = self._extract_risques(response_text)
        resume_executif = self._extract_resume(response_text)
        
        result = {
            "entreprise": self._normalize_company_data(company_data),
            "plan_action": {
                "resume_executif": resume_executif,
                "court_terme": court_terme,
                "moyen_terme": moyen_terme,
                "long_terme": long_terme,
                "kpis": kpis,
                "risques": risques
            },
            "metadonnees": self._create_metadata()
        }
        
        logger.info("Plan d'action structuré avec succès")
        return result
    
    def _extract_section(self, text: str, section_pattern: str, default_impact: str) -> List[Dict]:
        """
        Extrait une section du texte et crée des items structurés
        
        Args:
            text: Texte brut de la réponse Gemini
            section_pattern: Regex pattern pour identifier la section
            default_impact: Impact par défaut
            
        Returns:
            Liste des items structurés
        """
        items = []
        
        # Chercher la section
        section_match = re.search(
            f"{section_pattern}[:\s]*(.+?)(?=\n\n(?:points?|opportunit|risques?|actions?|mdonnées)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not section_match:
            logger.warning(f"Section non trouvée: {section_pattern}")
            return items
        
        section_content = section_match.group(1)
        
        # Splitter par items (numérotés ou tirets)
        item_pattern = r"(?:^|\n)\s*(?:\d+\.|-|\*)\s*(.+?)(?=\n\s*(?:\d+\.|-|\*)|\Z)"
        item_matches = re.finditer(item_pattern, section_content, re.MULTILINE | re.DOTALL)
        
        for i, match in enumerate(item_matches):
            item_text = match.group(1).strip()
            if not item_text:
                continue
            
            # Extraire titre et description
            lines = item_text.split('\n', 1)
            titre = lines[0].strip()
            description = lines[1].strip() if len(lines) > 1 else titre
            
            items.append({
                "titre": titre,
                "description": description,
                "impact": self._extract_impact(item_text, default_impact)
            })
        
        return items
    
    def _extract_actions(self, text: str, section_pattern: str, delai_par_defaut: int) -> List[Dict]:
        """
        Extrait les actions d'une section temporelle
        
        Args:
            text: Texte brut
            section_pattern: Pattern de la section
            delai_par_defaut: Délai par défaut en jours
            
        Returns:
            Liste des actions
        """
        actions = []
        
        section_match = re.search(
            f"{section_pattern}[:\s]*(.+?)(?=\n\n(?:court|moyen|long|risques?|KPI)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not section_match:
            logger.warning(f"Section action non trouvée: {section_pattern}")
            return actions
        
        section_content = section_match.group(1)
        
        # Extraire les actions
        action_pattern = r"(?:^|\n)\s*(?:\d+\.|-|\*)\s*(.+?)(?:\n|$)"
        action_matches = re.finditer(action_pattern, section_content, re.MULTILINE)
        
        for match in action_matches:
            action_text = match.group(1).strip()
            if not action_text:
                continue
            
            # Parser: "Action: description [priorité] [responsable]"
            titre, rest = self._split_titre_description(action_text)
            
            actions.append({
                "action": titre,
                "description": rest,
                "priorite": self._extract_priorite(action_text),
                "responsable": self._extract_responsable(action_text),
                "delai_jours": delai_par_defaut
            })
        
        return actions
    
    def _extract_kpis(self, text: str) -> List[Dict]:
        """Extrait les KPIs du texte"""
        kpis = []
        
        kpi_section = re.search(
            r"(?:KPI|indicateurs?|metrics?)[:\s]*(.+?)(?=\n\n(?:risques?|actions?)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not kpi_section:
            return kpis
        
        section_text = kpi_section.group(1)
        kpi_items = re.findall(r"(?:^|\n)\s*[-*]\s*(.+?)(?=\n|$)", section_text, re.MULTILINE)
        
        for item in kpi_items:
            if item.strip():
                kpis.append({
                    "metrique": item.strip(),
                    "baseline": None,
                    "cible": None,
                    "frequence_mesure": "mensuel"
                })
        
        return kpis
    
    def _extract_risques(self, text: str) -> List[Dict]:
        """Extrait les risques du texte"""
        risques = []
        
        risk_section = re.search(
            r"risques?[:\s]*(.+?)(?=\n\n(?:KPI|indicateurs?|actions?)|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if not risk_section:
            return risques
        
        section_text = risk_section.group(1)
        risk_items = re.findall(r"(?:^|\n)\s*(?:\d+\.|-|\*)\s*(.+?)(?=\n\s*(?:\d+\.|-|\*)|\Z)", 
                               section_text, re.MULTILINE | re.DOTALL)
        
        for item in risk_items:
            if item.strip():
                risques.append({
                    "risque": item.strip()[:100],
                    "probabilite": "modéré",
                    "impact": "majeur",
                    "mitigation": ""
                })
        
        return risques
    
    def _analyze_reviews(self, text: str) -> Optional[Dict]:
        """Analyse les thèmes des avis si présents"""
        if not text:
            return None
        
        return {
            "themes_positifs": [],
            "themes_negatifs": [],
            "sentiment_general": None
        }
    
    def _extract_resume(self, text: str) -> Optional[str]:
        """Extrait le résumé exécutif"""
        resume_match = re.search(
            r"(?:résumé\s+exécutif|summary)[:\s]*(.+?)(?=\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        return resume_match.group(1).strip() if resume_match else None
    
    def _extract_impact(self, text: str, default: str = Impact.MODERE) -> str:
        """Extrait le niveau d'impact du texte"""
        for impact in [Impact.CRITIQUE, Impact.MAJEUR, Impact.MODERE, Impact.FAIBLE]:
            if impact.value.lower() in text.lower():
                return impact.value
        return default
    
    def _extract_priorite(self, text: str, default: str = Priorite.P1) -> str:
        """Extrait la priorité du texte (P0, P1, P2, P3)"""
        for priority in [Priorite.P0, Priorite.P1, Priorite.P2, Priorite.P3]:
            if priority.value in text:
                return priority.value
        return default
    
    def _extract_responsable(self, text: str) -> Optional[str]:
        """Extrait le responsable estimé"""
        resp_match = re.search(r"responsable[:\s]*([^,\n]+)", text, re.IGNORECASE)
        return resp_match.group(1).strip() if resp_match else None
    
    def _split_titre_description(self, text: str) -> Tuple[str, str]:
        """Divise le texte en titre et description"""
        lines = text.split('\n', 1)
        titre = lines[0].strip()
        description = lines[1].strip() if len(lines) > 1 else ""
        return titre, description
    
    def _normalize_company_data(self, company_data: Dict) -> Dict:
        """Normalise les données d'entreprise de SerpAPI"""
        return {
            "id_entreprise": company_data.get("id", f"{self.company_name}_001"),
            "nom": company_data.get("name", self.company_name),
            "adresse": company_data.get("address", ""),
            "telephone": company_data.get("phone", None),
            "site_web": company_data.get("website", None),
            "categorie": company_data.get("type", None),
            "horaires": company_data.get("hours", None),
            "note_moyenne": company_data.get("rating", None),
            "nombre_avis": company_data.get("review_count", None),
            "photos": company_data.get("photos", [])
        }
    
    def _create_metadata(self) -> Dict:
        """Crée les métadonnées de l'analyse"""
        elapsed = (datetime.now() - self.start_time).total_seconds() * 1000
        
        return {
            "date_analyse": datetime.now().isoformat() + "Z",
            "version_prompt": self.version_prompt,
            "modele_gemini": self.model,
            "temps_reponse_ms": int(elapsed),
            "langue": "fr",
            "qualite_donnees": "acceptable",
            "id_analyse": f"ANAL-{self.company_name.upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        }
    
    def validate_against_schema(self, data: Dict, schema_path: str = None) -> Tuple[bool, List[str]]:
        """
        Valide les données contre le schéma JSON
        
        Args:
            data: Données à valider
            schema_path: Chemin du schéma JSON
            
        Returns:
            Tuple (is_valid, list_of_errors)
        """
        try:
            # Vérifications basiques
            required_keys = ["entreprise", "metadonnees"]
            
            errors = []
            for key in required_keys:
                if key not in data:
                    errors.append(f"Clé requise manquante: {key}")
            
            # Vérifier la structure de l'entreprise
            if "entreprise" in data:
                entreprise = data["entreprise"]
                if "nom" not in entreprise or "adresse" not in entreprise:
                    errors.append("Entreprise: nom et adresse requis")
            
            return len(errors) == 0, errors
        
        except Exception as e:
            logger.error(f"Erreur validation: {e}")
            return False, [str(e)]
