# =============================================================================
# File: repositories/protocols.py
# Purpose: Repository interface definitions (no implementations)
# =============================================================================

"""
Repository Protocols

Purpose:
--------
Defines abstract interfaces for data access.
Enables testing without concrete implementations.
Prevents coupling to specific ORMs or databases.

These are contracts, not implementations.
"""

from typing import Protocol, Dict, Any, List
from dataclasses import dataclass


@dataclass
class Case:
    """
    Domain model for a Case.
    
    Attributes:
    -----------
    case_id : str
        Unique case identifier
    current_state : str
        Current state in the state machine
    case_type : str
        Type/category of case (determines which rules apply)
    data : dict
        Raw case data fields
    """
    case_id: str
    current_state: str
    case_type: str
    data: Dict[str, Any]


class CaseRepository(Protocol):
    """
    Protocol for case data access.
    
    Implementations must provide case retrieval.
    """
    
    def get_case(self, case_id: str) -> Case:
        """
        Retrieve a case by ID.
        
        Parameters:
        -----------
        case_id : str
            Unique case identifier
            
        Returns:
        --------
        Case
            Complete case data
            
        Raises:
        -------
        CaseNotFoundError
            If case does not exist
        """
        ...


class RulesRepository(Protocol):
    """
    Protocol for rules data access.
    
    Implementations must provide rule retrieval by case type.
    """
    
    def get_active_rules(self, case_type: str) -> List[Dict[str, Any]]:
        """
        Retrieve active rules for a given case type.
        
        Parameters:
        -----------
        case_type : str
            Type of case (e.g., "loan_application", "claim_review")
            
        Returns:
        --------
        list[dict]
            List of rule definitions in Rule Engine format
            Each rule must have: rule_id, priority, enabled, condition, output_fact
            
        Notes:
        ------
        - Returns only enabled rules
        - Rules are NOT sorted (orchestrator handles priority)
        - Empty list is valid (no rules for case type)
        """
        ...

