import json
from typing import Dict, List, Any

class JSONExtractor:
    """Classe pour extraire et structurer les données de SerpAPI en JSON"""
    
    @staticmethod
    def extract_organic_results(raw_data: Dict) -> List[Dict[str, Any]]:
        """
        Extrait les résultats organiques de la réponse SerpAPI
        
        Args:
            raw_data: Les données brutes de SerpAPI
            
        Returns:
            Liste structurée des résultats
        """
        organic_results = []
        
        if "organic_results" in raw_data:
            for result in raw_data["organic_results"]:
                structured_result = {
                    "position": result.get("position"),
                    "title": result.get("title"),
                    "link": result.get("link"),
                    "snippet": result.get("snippet"),
                    "date": result.get("date")
                }
                organic_results.append(structured_result)
        
        return organic_results
    
    @staticmethod
    def extract_company_info(raw_data: Dict, company_name: str) -> Dict[str, Any]:
        """
        Extrait les informations complètes d'une entreprise
        
        Args:
            raw_data: Les données brutes de SerpAPI
            company_name: Nom de l'entreprise recherchée
            
        Returns:
            Dictionnaire structuré avec toutes les infos
        """
        structured_data = {
            "company": company_name,
            "search_metadata": {
                "status": raw_data.get("search_metadata", {}).get("status"),
                "processed_at": raw_data.get("search_metadata", {}).get("created_at"),
                "total_results": raw_data.get("search_information", {}).get("total_results")
            },
            "organic_results": JSONExtractor.extract_organic_results(raw_data),
            "knowledge_graph": raw_data.get("knowledge_graph", {}),
            "related_searches": [
                item.get("query") for item in raw_data.get("related_searches", [])
            ]
        }
        
        return structured_data
    
    @staticmethod
    def save_to_json(data: Dict, filename: str) -> bool:
        """
        Sauvegarde les données structurées dans un fichier JSON
        
        Args:
            data: Les données à sauvegarder
            filename: Nom du fichier JSON
            
        Returns:
            True si succès, False sinon
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde JSON: {e}")
            return False
    
    @staticmethod
    def validate_json_structure(data: Dict) -> bool:
        """
        Valide que la structure JSON est correcte
        
        Args:
            data: Les données à valider
            
        Returns:
            True si valide, False sinon
        """
        required_fields = ["company", "search_metadata", "organic_results"]
        
        for field in required_fields:
            if field not in data:
                print(f" Champ manquant: {field}")
                return False
        
        if not isinstance(data["organic_results"], list):
            print(" organic_results doit être une liste")
            return False
        
        return True