def apply_country_defaults(user_data: dict):
    if "_defaults_applied" in user_data:
        return

    country = user_data.get("country", "IN")

    defaults = {
        "IN": {
            "GLInflationRate": 6.0,
            "GLNormalFDRate": 7.0,
            "GLSrCitizenFDRate": 7.5
        },
        "US": {
            "GLInflationRate": 3.0,
            "GLNormalFDRate": 4.5,
            "GLSrCitizenFDRate": 4.0
        },
        "UK": {
            "GLInflationRate": 2.5,
            "GLNormalFDRate": 4.0,
            "GLSrCitizenFDRate": 4.2
        }
    }

    for field, value in defaults.get(country, {}).items():
        user_data.setdefault(field, {"input": value})

    user_data["_defaults_applied"] = True
