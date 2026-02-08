#def get_currency(user_data: dict) -> str:
#    base_context = user_data.get("base_context", {})
###    meta = base_context.get("_meta", {})
#    country = meta.get("country", "IN")
#    return {
#        "IN": "₹",
#        "US": "$",
#        "UK": "£"
#    }.get(country, "₹")

def get_currency(user_data):
    return {
        "IN": "₹",
        "US": "$",
        "UK": "£",
    }.get(user_data.get("country", "IN"), "₹")

