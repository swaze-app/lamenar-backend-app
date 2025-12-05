"""
Company extraction utilities - Extract company from email domain
"""
import re
from typing import Dict, Optional, List


def extract_domain_from_email(email: str) -> str:
    """
    Extract domain from email address
    
    Args:
        email: Email address (e.g., "john.doe@acmecorp.com")
        
    Returns:
        Domain (e.g., "acmecorp.com")
    """
    email_lower = email.lower().strip()
    if '@' not in email_lower:
        raise ValueError("Invalid email address")
    
    domain = email_lower.split('@')[-1]
    return domain


def split_camel_case(text: str) -> List[str]:
    """
    Split camelCase or concatenated words into separate words
    
    Examples:
        "acmecorp" -> ["acme", "corp"]
        "alphaEngineering" -> ["alpha", "engineering"]
        "techSolutions" -> ["tech", "solutions"]
    
    Args:
        text: Text to split
        
    Returns:
        List of words
    """
    if not text:
        return []
    
    words = []
    current_word = ""
    
    for i, char in enumerate(text):
        # If we encounter an uppercase letter (and it's not the first char)
        if char.isupper() and i > 0:
            # Save current word and start new one
            if current_word:
                words.append(current_word.lower())
            current_word = char
        else:
            current_word += char
    
    # Add the last word
    if current_word:
        words.append(current_word.lower())
    
    return words


def split_concatenated_words(text: str) -> List[str]:
    """
    Intelligently split concatenated words using common patterns
    
    Examples:
        "acmecorp" -> ["acme", "corp"]
        "alphacorp" -> ["alpha", "corp"]
        "techsolutions" -> ["tech", "solutions"]
    
    Args:
        text: Text to split
        
    Returns:
        List of words
    """
    # Common company suffixes/words to detect
    common_suffixes = [
        'corp', 'corporation', 'inc', 'incorporated', 'llc', 'ltd', 'limited',
        'tech', 'techs', 'solutions', 'systems', 'services', 'group', 'industries',
        'engineering', 'eng', 'international', 'global', 'enterprises', 'ventures'
    ]
    
    # Common prefixes
    common_prefixes = [
        'alpha', 'beta', 'gamma', 'delta', 'tech', 'digital', 'smart', 'global',
        'international', 'advanced', 'premium', 'elite', 'pro', 'max', 'ultra'
    ]
    
    text_lower = text.lower()
    
    # Try to find common suffixes first
    for suffix in sorted(common_suffixes, key=len, reverse=True):  # Longest first
        if text_lower.endswith(suffix) and len(text_lower) > len(suffix):
            prefix = text_lower[:-len(suffix)]
            if prefix:  # Make sure there's a prefix
                return [prefix, suffix]
    
    # Try to find common prefixes
    for prefix in sorted(common_prefixes, key=len, reverse=True):  # Longest first
        if text_lower.startswith(prefix) and len(text_lower) > len(prefix):
            suffix = text_lower[len(prefix):]
            if suffix:  # Make sure there's a suffix
                return [prefix, suffix]
    
    # If no pattern found, try camelCase splitting
    camel_words = split_camel_case(text)
    if len(camel_words) > 1:
        return camel_words
    
    # If still no split, try heuristic: look for common word boundaries
    # This is a simple approach - look for transitions from consonant to vowel patterns
    # For now, return as single word if we can't split intelligently
    return [text.lower()]


def format_domain_as_display_name(domain: str) -> str:
    """
    Convert domain to user-friendly company display name with intelligent word splitting
    
    Examples:
        "acmecorp.com" -> "Acme Corp"
        "alpha-engineering.com" -> "Alpha Engineering"
        "techSolutions.com" -> "Tech Solutions"
        "eng.acmecorp.com" -> "Acme Corp"
    
    Args:
        domain: Email domain (e.g., "acmecorp.com")
        
    Returns:
        Display name (e.g., "Acme Corp")
    """
    # Remove common TLDs
    name = domain
    tlds = ['.com', '.net', '.org', '.co', '.io', '.us', '.uk', '.in', '.au', '.co.uk', '.com.au']
    for tld in sorted(tlds, key=len, reverse=True):  # Longest first to catch .co.uk before .co
        if name.lower().endswith(tld):
            name = name[:-len(tld)]
            break
    
    # Handle subdomains - use root domain only
    # e.g., "eng.acmecorp.com" -> "acmecorp"
    parts = name.split('.')
    if len(parts) > 1:
        # Take the last meaningful part (usually the company name)
        name = parts[-1]
    
    # First, handle explicit separators (hyphens, underscores)
    if '-' in name or '_' in name:
        # Split on hyphens/underscores and process each part
        separator = '-' if '-' in name else '_'
        words = []
        for part in name.split(separator):
            if part:
                # Try to split concatenated words in each part
                split_words = split_concatenated_words(part)
                words.extend(split_words)
        # Capitalize each word
        return ' '.join(word.capitalize() for word in words if word)
    
    # No explicit separators, try to split concatenated words
    words = split_concatenated_words(name)
    
    # Capitalize each word
    display_name = ' '.join(word.capitalize() for word in words if word)
    
    return display_name


def extract_company_from_email(email: str) -> Dict[str, str]:
    """
    Extract company information from email address
    
    Args:
        email: Email address (e.g., "john.doe@acmecorp.com")
        
    Returns:
        Dictionary with:
        - domain: Full domain (e.g., "acmecorp.com")
        - normalized_company: Domain used for matching (e.g., "acmecorp.com")
        - display_name: User-friendly name (e.g., "Acme Corp")
    """
    domain = extract_domain_from_email(email)
    display_name = format_domain_as_display_name(domain)
    
    return {
        "domain": domain,
        "normalized_company": domain,  # Use full domain for uniqueness
        "display_name": display_name
    }


def normalize_company_domain(domain: str) -> str:
    """
    Normalize company domain for consistent matching
    
    Args:
        domain: Email domain
        
    Returns:
        Normalized domain (lowercase, trimmed)
    """
    return domain.lower().strip()

