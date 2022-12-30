def not_found(object_type):
    return (404, {"error": f"{object_type} not found"})

def missing_from_request(object_type):
    return (400, {"error": f"{object_type} missing from request"})
