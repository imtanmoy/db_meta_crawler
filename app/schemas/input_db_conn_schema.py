input_db_conn_schema = {
    "type": "object",
    "properties": {
        "dbtype": {
            "type": "string",
            "description": "Database type. Must Be one of these",
            "enum": ["mysql", "mssql", "postgresql"]
        },
        "username": {
            "type": "string",
            "description": "Database authentication user",
            "maxLength": 255,
            "minLength": 1
        },
        "password": {
            "type": "string",
            "description": "Database authentication password",
            "maxLength": 255,
            "minLength": 1
        },
        "hostname": {
            "type": "string",
            "description": "Database host address of The client",
            "minLength": 1,
            # "pattern": "^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$"
        },
        "dbname": {
            "type": "string",
            "description": "Database Name of The client",
            "minLength": 1
        }
    },
    "additionalProperties": False,
    "required": ["dbtype", "username", "password", "hostname", "dbname"]
}
