import os
import httpx
from typing import Optional, Dict, Any, List

POSTAL_API_URL = os.getenv("POSTAL_API_URL", "https://api.postalpincode.in/pincode/")

def fetch_postal_info_from_api(pincode: str) -> Optional[Dict[str, Any]]:
    """
    Fetches postal details for a 6-digit PIN code from the India Postal API.
    Handles multiple post offices under the same PIN.
    """
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return None
        
    url = f"{POSTAL_API_URL.rstrip('/')}/{pincode}"
    
    try:
        with httpx.Client(timeout=2.5) as client:
            response = client.get(url)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not isinstance(data, list) or len(data) == 0:
                return None
                
            entry = data[0]
            if entry.get("Status") != "Success" or not entry.get("PostOffice"):
                return None
                
            post_offices_data = entry["PostOffice"]
            first_po = post_offices_data[0]
            
            offices: List[Dict[str, Any]] = []
            for po in post_offices_data:
                offices.append({
                    "office_name": po.get("Name", "").strip(),
                    "office_type": po.get("BranchType", "").strip(),
                    "delivery_status": po.get("DeliveryStatus", "").strip(),
                    "district": po.get("District", "").strip(),
                    "state": po.get("State", "").strip()
                })
                
            return {
                "pincode": pincode,
                "district": first_po.get("District", "").strip(),
                "state": first_po.get("State", "").strip(),
                "region": first_po.get("Region", "").strip(),
                "division": first_po.get("Division", "").strip(),
                "circle": first_po.get("Circle", "").strip(),
                "country": first_po.get("Country", "India").strip(),
                "offices": offices
            }
    except Exception:
        # Offline resilience: if internet or API is unreachable, return None
        return None
