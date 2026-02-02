def pace_config(pace):
    if pace == "slow":
        return {"theory": 0.7, "practice": 0.3}
    if pace == "medium":
        return {"theory": 0.5, "practice": 0.5}
    return {"theory": 0.3, "practice": 0.7}

