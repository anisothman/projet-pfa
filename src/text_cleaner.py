"""
Module de nettoyage et normalisation du texte brut de Gemini

Classe TextCleaner pour:
- Supprimer les parasites (emojis, caractères spéciaux)
- Normaliser le texte (espaces, ponctuation, casse)
- Détecter sections mal formées
- Standardiser énumérations
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple
from logger_config import logger


class TextCleaner:
    """
    Nettoie et normalise les réponses brutes de Gemini
    
    Utilisage:
        cleaner = TextCleaner()
        clean_text = cleaner.clean_text(gemini_raw_response)
    """
    
    def __init__(self, aggressive: bool = False):
        """
        Initialise le cleaner
        
        Args:
            aggressive: Si True, nettoyage agressif (supprime plus de contenu)
        """
        self.aggressive = aggressive
        self.logger = logger
    
    def clean_text(self, text: str) -> str:
        """
        Nettoie le texte brut principal
        
        Args:
            text: Texte brut de Gemini
            
        Returns:
            Texte nettoyé et normalisé
        """
        if not text or not isinstance(text, str):
            return ""
        
        self.logger.info("Nettoyage du texte brut Gemini...")
        
        # 1. Supprimer emojis et caractères spéciaux
        text = self._remove_emojis(text)
        
        # 2. Supprimer balises HTML/Markdown inutiles
        text = self._remove_html_tags(text)
        
        # 3. Normaliser la casse des délimiteurs
        text = self._normalize_delimiters(text)
        
        # 4. Nettoyer les espaces excessifs
        text = self._clean_whitespace(text)
        
        # 5. Normaliser la ponctuation
        text = self._normalize_punctuation(text)
        
        # 6. Normaliser les énumérations
        text = self._normalize_enumerations(text)
        
        # 7. Normaliser les énumérations d'impact/priorité
        text = self._normalize_enums(text)
        
        self.logger.info("Texte nettoyé avec succès")
        return text
    
    def _remove_emojis(self, text: str) -> str:
        """Supprime les emojis et caractères spéciaux"""
        # Pattern pour emojis (US + étendu)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Symbols & pictographs
            "\U0001F680-\U0001F6FF"  # Transport & map
            "\U0001F1E0-\U0001F1FF"  # Flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"                 # Dingbats
            "\u3030"
            "]",
            flags=re.UNICODE
        )
        
        clean = emoji_pattern.sub(r'', text)
        
        # Supprimer aussi les caractères de contrôle
        clean = ''.join(char for char in clean 
                       if unicodedata.category(char)[0] != 'C')
        
        return clean
    
    def _remove_html_tags(self, text: str) -> str:
        """Supprime les balises HTML/Markdown inutiles"""
        # Remplacer ***text*** par text
        text = re.sub(r'\*{2,}([^*]+)\*{2,}', r'\1', text)
        # Remplacer **text** par text
        text = re.sub(r'\*{1}([^*]+)\*{1}', r'\1', text)
        # Remplacer __text__ par text
        text = re.sub(r'_{2,}([^_]+)_{2,}', r'\1', text)
        # Remplacer _text_ par text
        text = re.sub(r'_{1}([^_]+)_{1}', r'\1', text)
        # Remplacer `code` par code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Supprimer balises HTML
        text = re.sub(r'<[^>]+>', '', text)
        # Remplacer [link](url) par link
        text = re.sub(r'\[([^\]]+)\]\([^\)]*\)', r'\1', text)
        
        return text
    
    def _normalize_delimiters(self, text: str) -> str:
        """Normalise les délimiteurs de sections"""
        # Remplacer variantes de POINTS FORTS
        text = re.sub(
            r'(?i)(points?\s+forts?|strengths?|avantages?|atouts?)[:\s]*',
            'POINTS FORTS:',
            text
        )
        # Remplacer variantes de POINTS FAIBLES
        text = re.sub(
            r'(?i)(points?\s+faibles?|weaknesses?|faiblesses?|inconvénients?)[:\s]*',
            'POINTS FAIBLES:',
            text
        )
        # Remplacer variantes d'OPPORTUNITÉS
        text = re.sub(
            r'(?i)(opportunit[éè]s?|opportunities?)[:\s]*',
            'OPPORTUNITÉS:',
            text
        )
        # Remplacer variantes d'ACTIONS COURT TERME
        text = re.sub(
            r'(?i)(actions?\s+court\s+terme|short\s+term|0-3\s+mois)[:\s]*',
            'ACTIONS COURT TERME (0-3 mois):',
            text
        )
        # Remplacer variantes d'ACTIONS MOYEN TERME
        text = re.sub(
            r'(?i)(actions?\s+moyen\s+terme|medium\s+term|3-6\s+mois)[:\s]*',
            'ACTIONS MOYEN TERME (3-6 mois):',
            text
        )
        # Remplacer variantes d'ACTIONS LONG TERME
        text = re.sub(
            r'(?i)(actions?\s+long\s+terme|long\s+term|6-12\s+mois)[:\s]*',
            'ACTIONS LONG TERME (6-12 mois):',
            text
        )
        # Remplacer variantes de KPI
        text = re.sub(
            r'(?i)(kpis?|indicateurs?|metrics?|key\s+performance)[:\s]*',
            'KPIs:',
            text
        )
        # Remplacer variantes de RISQUES
        text = re.sub(
            r'(?i)(risques?|risks?|dangers?)[:\s]*',
            'RISQUES:',
            text
        )
        # Remplacer variantes RÉSUMÉ EXÉCUTIF
        text = re.sub(
            r'(?i)(résumé\s+exécutif|executive\s+summary|summary)[:\s]*',
            'RÉSUMÉ EXÉCUTIF:',
            text
        )
        
        return text
    
    def _clean_whitespace(self, text: str) -> str:
        """Nettoie les espaces excessifs"""
        # Supprimer espaces au début/fin
        text = text.strip()
        
        # Supprimer espaces multiples (plusieurs espaces → 1)
        text = re.sub(r' +', ' ', text)
        
        # Supprimer retours à la ligne excessifs (3+ → 1)
        text = re.sub(r'\n\n\n+', '\n\n', text)
        
        # Supprimer espace avant ponctuation
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        
        # Normaliser les tirets et traits de soulignement au début de lignes
        text = re.sub(r'\n\s*[-_*]+\s*\n', '\n', text)
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalise la ponctuation"""
        # Remplacer guillemets variantes
        text = re.sub(r'[`´"„"‟]', '"', text)
        text = re.sub(r'[''‛′]', "'", text)
        
        # Normaliser tirets
        text = re.sub(r'[–—−]', '-', text)
        
        # Normaliser ellipsis
        text = re.sub(r'\.{4,}', '...', text)
        text = re.sub(r'… +', '... ', text)
        
        # Normaliser espaces avant paren/crochet
        text = re.sub(r'\s+\(', ' (', text)
        text = re.sub(r'\s+\[', ' [', text)
        
        return text
    
    def _normalize_enumerations(self, text: str) -> str:
        """Normalise le formatage des énumérations"""
        # Normaliser les numérotations (1., 1), 1:, 1-, etc. → 1.)
        text = re.sub(
            r'(?m)^[\s]*(?:[\d]+[.):\-\s]+)',
            lambda m: f"{m.group(0)[0:1]}\n",
            text
        )
        
        # Normaliser les tirets (-,*,•,◦,etc. → -)
        text = re.sub(r'(?m)^[\s]*[*•◦○●]+\s+', '- ', text)
        
        return text
    
    def _normalize_enums(self, text: str) -> str:
        """Normalise les énumérations (CRITIQUE, P0, etc.)"""
        # Normaliser CRITIQUE/CRITICAL
        text = re.sub(r'(?i)(critique|critical|critical\s+level|très.*haute|highest)',
                     'CRITIQUE', text)
        
        # Normaliser MAJEUR/MAJOR
        text = re.sub(r'(?i)(majeur|major|high|haute|important)',
                     'MAJEUR', text)
        
        # Normaliser MODÉRÉ/MODERATE
        text = re.sub(r'(?i)(modéré|moderate|medium|moyenne)',
                     'MODÉRÉ', text)
        
        # Normaliser FAIBLE/LOW
        text = re.sub(r'(?i)(faible|low|minor|bas|basse|weak)',
                     'FAIBLE', text)
        
        # Normaliser P0-P3
        text = re.sub(r'(?i)(p0|p-0|p 0|priority 0|urgent|critical)',
                     'P0', text)
        text = re.sub(r'(?i)(p1|p-1|p 1|priority 1|high)',
                     'P1', text)
        text = re.sub(r'(?i)(p2|p-2|p 2|priority 2|medium)',
                     'P2', text)
        text = re.sub(r'(?i)(p3|p-3|p 3|priority 3|low)',
                     'P3', text)
        
        # Normaliser TRÈS ÉLEVÉ/ÉLEVÉ
        text = re.sub(r'(?i)(très.*élevé|very.*high|very.*strong|extrêmement)',
                     'TRÈS ÉLEVÉ', text)
        text = re.sub(r'(?i)(^|\s)(élevé|high|strong|significant)(\s|$)',
                     r'\1ÉLEVÉ\3', text)
        
        return text
    
    def remove_duplicates(self, text: str) -> str:
        """Supprime les lignes dupliquées"""
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped and stripped not in seen:
                seen.add(stripped)
                unique_lines.append(line)
            elif not stripped:
                # Garder les lignes vides (une par une)
                if not unique_lines or unique_lines[-1].strip() != '':
                    unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def detect_sections(self, text: str) -> Dict[str, Tuple[int, int]]:
        """
        Détecte les positions des sections dans le texte
        
        Args:
            text: Texte nettoyé
            
        Returns:
            Dict avec section → (start_pos, end_pos)
        """
        sections = {}
        
        patterns = {
            'points_forts': r'POINTS FORTS:',
            'points_faibles': r'POINTS FAIBLES:',
            'opportunites': r'OPPORTUNITÉS:',
            'resume_executif': r'RÉSUMÉ EXÉCUTIF:',
            'court_terme': r'ACTIONS COURT TERME',
            'moyen_terme': r'ACTIONS MOYEN TERME',
            'long_terme': r'ACTIONS LONG TERME',
            'kpis': r'KPIs:',
            'risques': r'RISQUES:'
        }
        
        for section_name, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = match.start()
                # Trouver la fin (prochaine section ou fin du texte)
                rest_text = text[match.end():]
                next_section = re.search(
                    r'(POINTS FORTS:|POINTS FAIBLES:|OPPORTUNITÉS:|'
                    r'ACTIONS COURT TERME|ACTIONS MOYEN TERME|'
                    r'ACTIONS LONG TERME|KPIs:|RISQUES:|RÉSUMÉ)',
                    rest_text,
                    re.IGNORECASE
                )
                end = match.end() + next_section.start() if next_section else len(text)
                sections[section_name] = (start, end)
        
        return sections
    
    def get_section_content(self, text: str, section_name: str) -> Optional[str]:
        """
        Extrait le contenu d'une section
        
        Args:
            text: Texte nettoyé
            section_name: Nom de la section (ex: 'points_forts')
            
        Returns:
            Contenu de la section ou None
        """
        sections = self.detect_sections(text)
        
        if section_name in sections:
            start, end = sections[section_name]
            return text[start:end].strip()
        
        return None
    
    def full_pipeline(self, text: str) -> Dict:
        """
        Lance le pipeline complet de nettoyage
        
        Args:
            text: Texte brut de Gemini
            
        Returns:
            Dict avec:
                - clean_text: Texte nettoyé
                - sections: Sections détectées
                - sections_content: Contenu de chaque section
        """
        clean = self.clean_text(text)
        clean = self.remove_duplicates(clean)
        sections = self.detect_sections(clean)
        
        sections_content = {}
        for section_name in sections.keys():
            content = self.get_section_content(clean, section_name)
            if content:
                sections_content[section_name] = content
        
        return {
            'clean_text': clean,
            'sections': sections,
            'sections_content': sections_content,
            'quality_score': self._calculate_quality_score(clean, sections)
        }
    
    def _calculate_quality_score(self, text: str, sections: Dict) -> float:
        """
        Calcule un score de qualité du texte nettoyé
        
        Args:
            text: Texte nettoyé
            sections: Sections détectées
            
        Returns:
            Score entre 0 et 100
        """
        score = 0
        
        # 30 points si au moins 3 sections détectées
        if len(sections) >= 3:
            score += 30
        elif len(sections) >= 1:
            score += 15
        
        # 30 points si pas trop de parenthèses mal fermées
        open_parens = text.count('(')
        close_parens = text.count(')')
        if open_parens == close_parens:
            score += 30
        elif abs(open_parens - close_parens) <= 2:
            score += 15
        
        # 20 points si bonne longueur (> 500 chars)
        if len(text) > 500:
            score += 20
        elif len(text) > 200:
            score += 10
        
        # 20 points si énumérations détectées
        if re.search(r'^[\s]*\d+\.', text, re.MULTILINE):
            score += 20
        elif re.search(r'^[\s]*-', text, re.MULTILINE):
            score += 10
        
        return min(100, score)


# ============================================================================
# EXEMPLES DE TEST
# ============================================================================

if __name__ == "__main__":
    # Test 1: Texte sale avec emojis
    dirty_text = """
    🔥 POINTS FORTS!!!
    
    ok so apple has like... a really strong brand (CRITIQUE/HIGH) 
    description: the company is known for... **lots of stuff**
    
    plus they have INNOVATION & R&D    (  CRITICAL  )
    [description]... they invest heavily in R&D
    
    POINTS FAIBLES:
    * dépendance aux fournisseurs (MAJEUR)
    * prix too expensive (high impact)
    
    RÉSUMÉ EXÉCUTIF
    Apple needs to focus on innovation and expand to new markets.
    """
    
    cleaner = TextCleaner()
    result = cleaner.full_pipeline(dirty_text)
    
    print("=" * 60)
    print("RÉSULTAT DU NETTOYAGE")
    print("=" * 60)
    print(f"\n✓ Texte nettoyé:")
    print(result['clean_text'])
    print(f"\n✓ Sections détectées: {list(result['sections'].keys())}")
    print(f"✓ Score qualité: {result['quality_score']}/100")
