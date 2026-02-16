"""
Module 2: Structure Parser

This module parses the "Clinical Indications for Admission" section and extracts
individual criteria with their components, qualifiers, and references.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple


logger = logging.getLogger(__name__)


class CriteriaParser:
    """
    Parses MCG admission criteria from extracted PDF text.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize parser with configuration.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.section_headers = config.get('parser', {}).get('section_headers', [])
    
    def parse_admission_criteria(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse admission criteria from extracted PDF data.
        
        Args:
            extracted_data: Output from module_1_pdf_extraction
            
        Returns:
            Structured criteria dictionary
        """
        logger.info("Starting admission criteria parsing")
        
        # Find the admission criteria section
        admission_section = self._find_section(
            extracted_data['sections'], 
            "Clinical Indications for Admission to Inpatient Care"
        )
        
        if not admission_section:
            logger.warning("Could not find admission criteria section")
            return {
                "admission_criteria": {
                    "rule_type": "one_or_more",
                    "criteria_list": []
                },
                "alternatives_to_admission": []
            }
        
        # Parse criteria from section text
        criteria_list = self._extract_criteria_list(
            admission_section['raw_text']
        )
        
        # Parse alternatives section
        alternatives_section = self._find_section(
            extracted_data['sections'],
            "Alternatives to Admission"
        )
        alternatives = self.parse_alternatives(
            alternatives_section['raw_text'] if alternatives_section else ""
        )
        
        result = {
            "admission_criteria": {
                "rule_type": "one_or_more",
                "criteria_list": criteria_list
            },
            "alternatives_to_admission": alternatives
        }
        
        logger.info(f"Parsed {len(criteria_list)} admission criteria")
        return result
    
    def _find_section(self, sections: List[Dict], section_name: str) -> Optional[Dict]:
        """
        Find a specific section by name.
        
        Args:
            sections: List of section dictionaries
            section_name: Name of section to find
            
        Returns:
            Section dictionary or None
        """
        for section in sections:
            if section_name.lower() in section['section_name'].lower():
                # Skip empty sections (bug fix for duplicate empty sections from module_1)
                if section.get('raw_text', '').strip():
                    return section
        return None
    
    def _extract_criteria_list(self, section_text: str) -> List[Dict[str, Any]]:
        """
        Extract individual criteria from section text.
        
        Args:
            section_text: Raw text of admission criteria section
            
        Returns:
            List of parsed criterion dictionaries
        """
        criteria_list = []
        
        # Split by bullet points or numbered items
        # Common patterns: •, -, *, numbers followed by period or parenthesis
        lines = section_text.split('\n')
        
        current_criterion = None
        current_criterion_int_id = None
        criterion_id = 1
        in_criteria_section = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if we've reached the criteria introduction line
            if re.search(r'(admission|indicated|following).*:', line, re.IGNORECASE) and not in_criteria_section:
                in_criteria_section = True
                continue
            
            # Skip common non-criteria patterns
            is_skip_line = (
                line.startswith('http') or
                line.startswith('Page ') or
                line.startswith('ISC -') or
                re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}', line) or  # Date
                len(line) > 200  # Likely a paragraph, not a criterion
            )
            
            if is_skip_line:
                continue
            
            # Check if this is a new criterion (starts with bullet or number)
            is_new_criterion = (
                re.match(r'^[•●○■□▪▫◦‣⁃-]\s+', line) or
                re.match(r'^\d+[\.)]\s+', line) or
                re.match(r'^[a-z][\.)]\s+', line, re.IGNORECASE)
            )
            
            # If we're in the criteria section and no explicit bullets, treat lines as criteria
            # if they start with capital letter and are of reasonable length
            if not is_new_criterion and in_criteria_section:
                if len(line) < 15:  # Too short to be a criterion
                    continue
                if not line[0].isupper():  # Continuation of previous line
                    if current_criterion:
                        current_criterion['criterion_text'] += ' ' + line
                        updated = self.extract_criterion_components(
                            current_criterion['criterion_text'],
                            current_criterion_int_id
                        )
                        current_criterion.update(updated)
                    continue
                # Treat as new criterion
                is_new_criterion = True
            
            if is_new_criterion:
                # Save previous criterion
                if current_criterion:
                    criteria_list.append(current_criterion)
                
                # Start new criterion
                criterion_text = re.sub(r'^[•●○■□▪▫◦‣⁃-]\s+', '', line)
                criterion_text = re.sub(r'^\d+[\.)]\s+', '', criterion_text)
                criterion_text = re.sub(r'^[a-z][\.)]\s+', '', criterion_text, flags=re.IGNORECASE)
                
                current_criterion_int_id = criterion_id
                current_criterion = self.extract_criterion_components(
                    criterion_text, 
                    criterion_id
                )
                criterion_id += 1
            elif current_criterion:
                # Continue previous criterion (multi-line)
                current_criterion['criterion_text'] += ' ' + line
                # Re-extract components with updated text
                updated = self.extract_criterion_components(
                    current_criterion['criterion_text'],
                    current_criterion_int_id
                )
                current_criterion.update(updated)
        
        # Add final criterion
        if current_criterion:
            criteria_list.append(current_criterion)
        
        return criteria_list
    
    def extract_criterion_components(
        self, 
        criterion_text: str, 
        criterion_id: int
    ) -> Dict[str, Any]:
        """
        Extract components from a single criterion.
        
        Args:
            criterion_text: Text of the criterion
            criterion_id: Unique identifier for criterion
            
        Returns:
            Dictionary with extracted components
        """
        # Extract primary condition (first part before qualifiers)
        primary_condition = self._extract_primary_condition(criterion_text)
        
        # Extract qualifiers (severe, persistent, acute, etc.)
        qualifiers = self._extract_qualifiers(criterion_text)
        
        # Extract conditional requirements
        conditional_requirements = self._extract_conditional_requirements(criterion_text)
        
        # Extract persistence/temporal requirements
        persistence_requirement = self._extract_persistence(criterion_text)
        
        # Extract evidence citations
        evidence_citations = self._extract_evidence_citations(criterion_text)
        
        # Determine clinical category
        clinical_category = self._determine_clinical_category(criterion_text)
        
        return {
            "criterion_id": f"criterion_{criterion_id:03d}",
            "criterion_text": criterion_text.strip(),
            "primary_condition": primary_condition,
            "qualifiers": qualifiers,
            "conditional_requirements": conditional_requirements,
            "persistence_requirement": persistence_requirement,
            "evidence_citations": evidence_citations,
            "clinical_category": clinical_category
        }
    
    def _extract_primary_condition(self, text: str) -> str:
        """
        Extract the primary clinical condition from criterion text.
        
        Args:
            text: Criterion text
            
        Returns:
            Primary condition string
        """
        # Remove qualifiers and take first clause
        text_clean = re.sub(r'\([^)]*\)', '', text)  # Remove parentheticals
        text_clean = re.sub(r'\[[^\]]*\]', '', text_clean)  # Remove brackets
        
        # Take text before common conjunctions
        primary = re.split(r'\s+(?:and|or|with|that|requiring|despite)\s+', text_clean)[0]
        
        return primary.strip()
    
    def _extract_qualifiers(self, text: str) -> List[str]:
        """
        Extract qualifiers like 'severe', 'persistent', 'acute'.
        
        Args:
            text: Criterion text
            
        Returns:
            List of qualifier strings
        """
        qualifiers = []
        
        qualifier_patterns = [
            r'\b(severe|mild|moderate|major|minor)\b',
            r'\b(persistent|intermittent|acute|chronic|recurrent)\b',
            r'\b(progressive|worsening|deteriorating|improving)\b',
            r'\b(new|ongoing|recent|sudden)\b',
            r'\b(refractory|resistant|unresponsive)\b'
        ]
        
        for pattern in qualifier_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            qualifiers.extend([m.lower() for m in matches])
        
        return list(set(qualifiers))
    
    def _extract_conditional_requirements(self, text: str) -> List[str]:
        """
        Extract conditional requirements (e.g., "if blood cultures performed").
        
        Args:
            text: Criterion text
            
        Returns:
            List of conditional requirement strings
        """
        conditionals = []
        
        # Pattern for "if", "when", "requiring", "despite"
        conditional_patterns = [
            r'(?:if|when|where)\s+([^,;.]+)',
            r'despite\s+([^,;.]+)',
            r'requiring\s+([^,;.]+)',
            r'with\s+([^,;.]+\s+(?:performed|administered|given))'
        ]
        
        for pattern in conditional_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            conditionals.extend([m.strip() for m in matches])
        
        return conditionals
    
    def _extract_persistence(self, text: str) -> str:
        """
        Extract temporal/persistence requirements.
        
        Args:
            text: Criterion text
            
        Returns:
            Persistence requirement string
        """
        persistence_patterns = [
            r'(?:persists?|persisting|persist)\s+(?:after|despite|for)\s+([^,;.]+)',
            r'(?:that|which)\s+(?:persists?|persisting)',
            r'ongoing\s+(?:after|despite|for)\s+([^,;.]+)',
            r'continues?\s+(?:after|despite|for)\s+([^,;.]+)'
        ]
        
        for pattern in persistence_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.groups():
                    return f"persists {match.group(1).strip()}"
                else:
                    return "persistent"
        
        return ""
    
    def _extract_evidence_citations(self, text: str) -> List[int]:
        """
        Extract evidence citation numbers.
        
        Args:
            text: Criterion text
            
        Returns:
            List of citation numbers
        """
        # Look for patterns like (6), (7), (8) that are likely citations
        citations = re.findall(r'\((\d+)\)', text)
        return [int(c) for c in citations]
    
    def _determine_clinical_category(self, text: str) -> str:
        """
        Determine clinical category of the criterion.
        
        Args:
            text: Criterion text
            
        Returns:
            Clinical category string
        """
        text_lower = text.lower()
        
        # Map keywords to categories
        category_keywords = {
            "hemodynamic": ["hemodynamic", "blood pressure", "hypotension", "shock", "bp"],
            "respiratory": ["respiratory", "hypoxemia", "oxygen", "breathing", "dyspnea", "tachypnea"],
            "mental_status": ["mental status", "altered", "confusion", "delirium", "consciousness"],
            "laboratory": ["laboratory", "lab", "coagulopathy", "platelet", "culture"],
            "metabolic": ["dehydration", "hydration", "fluid", "electrolyte"],
            "organ_dysfunction": ["organ dysfunction", "end organ", "organ failure"],
            "vital_signs": ["temperature", "heart rate", "pulse", "vital"],
            "infectious": ["bacteremia", "sepsis", "infection", "fever"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"
    
    def parse_alternatives(self, section_text: str) -> List[Dict[str, Any]]:
        """
        Parse alternatives to admission section.
        
        Args:
            section_text: Raw text of alternatives section
            
        Returns:
            List of alternative care options
        """
        if not section_text:
            return []
        
        alternatives = []
        lines = section_text.split('\n')
        
        current_alternative = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a new alternative
            is_new_alternative = (
                re.match(r'^[•●○■□▪▫◦‣⁃-]\s+', line) or
                re.match(r'^\d+[\.)]\s+', line)
            )
            
            if is_new_alternative:
                if current_alternative:
                    alternatives.append(current_alternative)
                
                # Extract alternative text
                alt_text = re.sub(r'^[•●○■□▪▫◦‣⁃-]\s+', '', line)
                alt_text = re.sub(r'^\d+[\.)]\s+', '', alt_text)
                
                current_alternative = {
                    "alternative_id": f"alt_{len(alternatives) + 1:03d}",
                    "alternative_text": alt_text.strip(),
                    "care_setting": self._determine_care_setting(alt_text)
                }
            elif current_alternative:
                current_alternative["alternative_text"] += ' ' + line
        
        if current_alternative:
            alternatives.append(current_alternative)
        
        logger.info(f"Parsed {len(alternatives)} alternatives to admission")
        return alternatives
    
    def _determine_care_setting(self, text: str) -> str:
        """
        Determine care setting from alternative text.
        
        Args:
            text: Alternative text
            
        Returns:
            Care setting string
        """
        text_lower = text.lower()
        
        if "observation" in text_lower:
            return "observation_unit"
        elif "emergency" in text_lower or "ed " in text_lower:
            return "emergency_department"
        elif "outpatient" in text_lower:
            return "outpatient"
        elif "home" in text_lower:
            return "home_care"
        elif "infusion" in text_lower:
            return "infusion_center"
        else:
            return "alternative_care"


def parse_admission_criteria(extracted_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to parse admission criteria.
    
    Args:
        extracted_data: Output from module_1_pdf_extraction
        config: Configuration dictionary
        
    Returns:
        Parsed criteria dictionary
    """
    parser = CriteriaParser(config)
    return parser.parse_admission_criteria(extracted_data)


if __name__ == "__main__":
    # Test the module independently
    import yaml
    from module_1_pdf_extraction import extract_pdf_content
    
    logging.basicConfig(level=logging.INFO)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract PDF first
    pdf_path = r"uploads\mcg-guidelines\MCG Sepsis and Other Febrile Illness, without Focal Infection (1).pdf"
    
    try:
        extracted_data = extract_pdf_content(pdf_path, config)
        parsed_data = parse_admission_criteria(extracted_data, config)
        
        print(f"\nParsed {len(parsed_data['admission_criteria']['criteria_list'])} criteria")
        print(f"Found {len(parsed_data['alternatives_to_admission'])} alternatives")
        
        # Show first criterion as example
        if parsed_data['admission_criteria']['criteria_list']:
            criterion = parsed_data['admission_criteria']['criteria_list'][0]
            print(f"\nExample criterion:")
            print(f"  ID: {criterion['criterion_id']}")
            print(f"  Text: {criterion['criterion_text'][:100]}...")
            print(f"  Category: {criterion['clinical_category']}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
