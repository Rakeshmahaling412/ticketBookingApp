from cpla_flask_admin.util.admin_view_secured import describe_scope, central_security

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Application Permissions setup
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# (We do not use the term 'role' & 'permission' on purpose, are they are confusing in the way people used them at socgen)
'''
__objects = describe_objects(
    data='data (news, websites, files)',
    referential='referential (trees, fields)',
    security='technical user data (logins, logs, security)')

__supreme_objects = {
    'referential',
    'security',
    'special'
}

__entities = {
    'data': {
        'HKG': 'Hong-Kong based-entities',
        'HKGS': 'Hong-Kong securities',
        'SGP': 'Singapore branch',
        'SGPS': 'Singapore Securities entity',
        'THA': 'Thailand based-entities',
        'THAS': 'Thailand Securities',
        'AUS': 'Australia based-entities',
        'AUSS': 'Australia securities entity',
        'KOR': 'Korea branch',
        'KORS': 'Korea Securities entity',
        'TWN': 'Taiwan branch',
        'TWNS': 'Taiwan Securities entity',
        'JPN': 'JAPAN branch',
        'JPNS': 'JAPAN Securities entity',
        'CHN': 'China branch',
        'IDN': 'Jakarta branch',
        'IND': 'India branch',
        'INDS': 'India securities branch',
        'VNM': 'Vietnam branch entity',
        'MYS': 'Kuala Lumpur branch',
    }
}

central_security.scopes = define_scopes_as_combination(__objects, __entities)

central_security.profiles = {
    **{
        'Administrator': 'Special maintenance rights for developers and IT supports',
        'Organizer': describe_scope('write', __objects['referential']),
    },
    **{en_key + ' Producer': describe_scope('read & write', __objects['data'], en_desc) for en_key, en_desc in
       __entities['data'].items()}
}

central_security.profiles_to_scopes = {
    **{
        'Administrator': ['special', 'read-security', 'write-security'],
        'Organizer': ['read-referential', 'write-referential'],
    },
    **{en_key + ' Producer': [op + '-data-' + en_key for op in ['read', 'write']] for en_key, en_desc in
       __entities['data'].items()}
}

'''

__objects = {
    'employee': 'employee table',
    'referential': 'referential (trees, fields)',
    'security': 'technical user data (logins, logs, security)',
    'breach': 'breach table',
    'special': 'unsafely manipulate',
    'nothing': 'void',
    'data': '1.0 data'
}

__superme_objects = {
    'manager-special',
    'referential',
    'security',
    'special',
    'nothing'
}

entities_lst = {
                "SOCIETE GENERALE, London Branch": 'SOCIETE GENERALE, London Branch',
                "Société Générale Luxembourg": 'Société Générale Luxembourg',
                "SOCIETE GENERALE SUCCURSAL EN ESPANA": 'SOCIETE GENERALE SUCCURSAL EN ESPANA',
                "SG FRANCFORT": 'SG FRANCFORT',
                "SG ISTANBUL": 'SG ISTANBUL',
                "SG ZÜRICH": 'SG ZÜRICH',
                "SG BRUXELLES": 'SG BRUXELLES',
                "Société Générale Securities Services GmbH": 'Société Générale Securities Services GmbH',
                "SG MILAN": 'SG MILAN',
                "SOCIETE GENERALE, DIFC BRANCH": 'SOCIETE GENERALE, DIFC BRANCH',
                "SOCIETE GENERALE - FORGE": 'SOCIETE GENERALE - FORGE',
                "SG DUBLIN": 'SG DUBLIN',
                "SG AMSTERDAM": 'SG AMSTERDAM',
                "Societe Generale Securities Services, SGSS (Ireland) Limited": 'Societe Generale Securities Services, SGSS (Ireland) Limited',
                "Société Générale Saudi Arabia JSC": 'Société Générale Saudi Arabia JSC',
                "SG VIENNE": 'SG VIENNE',
                "SOCIETE GENERALE IMMOBEL": 'SOCIETE GENERALE IMMOBEL',
                "SOCIETE GENERALE": 'SOCIETE GENERALE',
                "SOCIETE GENERALE GLOBAL SOLUTION CENTRE INDIA": "SOCIETE GENERALE GLOBAL SOLUTION CENTRE INDIA",
                "SG STOCKHOLM": "SG STOCKHOLM",
                "SG OPTION EUROPE": 'SG OPTION EUROPE',
                "SG JOHANNESBURG": 'SG JOHANNESBURG',
                "SOCGEN FINANCIACIONES IBERIA, SL": "SOCGEN FINANCIACIONES IBERIA, SL",
                "SOCIETE GENERALE INTERNATIONAL LIMITED" : "SOCIETE GENERALE INTERNATIONAL LIMITED",
                "Société Générale SA Oddzial w Polsce" : "Société Générale SA Oddzial w Polsce",
                "Société Générale Securities Services Spa" : "Société Générale Securities Services Spa",
                "Société Générale Factoring": "Société Générale Factoring",   # For business unit: Start with 'BU:'#
                'Region:EMEA': 'Applicable to EMEA',
                'Region:APAC': 'Applicable to APAC',
                'BPO:CPLE': 'CPLE',
                'BPO:DCS Cybersecurity': 'DCS Cybersecurity',
                'BPO:GTPS': 'GTPS Specific',
                'BPO:GBTO': 'GBTO Specific',
                'BPO:MARK': 'MARK Specific',
                'BPO:GLBA': 'GLBA Specific',
                'BPO:COM': 'COM Specific',
                'BPO:DFIN': 'DFIN Specific',
                'BPO:GBSU': 'GBSU Specific',
                'BPO:GCOO': 'GCOO Specific',
                'BPO:GSCP': 'GSCP Specific',
                'BPO:HUMN': 'HUMN Specific',
                'BPO:IGAD': 'IGAD Specific',
                'BPO:PRIV': 'PRIV Specific',
                'BPO:RISQ': 'RISQ Specific',
                'BPO:SEGL': 'SEGL Specific',
                'BPO:DIR': 'DIR Specific',
                'BPO:TRS': 'TRS Specific',
                'BPO:ZOLD': 'ZOLD Specific',
                'BPO:GBIS/DIR/CSO': 'GBIS/DIR/CSO Specific'
                }

__entities = {
    **{obj: entities_lst if obj not in __superme_objects else {} for obj in
       __objects}

}

__operation_matrix = {
    'employee': {'read', 'edit'},
    'breach': {'read', 'edit', 'create'},
    'referential': {'read', 'write'},
    'security': {'read', 'write'},
    'special': {},
    'manager-special': {},
    'nothing': {'read'},
    'data': {'read', 'write'}
}


def define_scopes_as_combination(objects, entities, operation_matrix, *args):
    """
    There are 3 operations on the objects. Read is read-only. Write is read-write.
    Configure is for Feed Administrator to configure the feed from GUI including steps, filter and log on'
    System does not differentiate referential and security based on entity
    Format of scope: {op-obj-entity} e.g. read-data-HKG, read-security
    TODO: update main.views.get_entity_from_constraints
    """
    # all = {None: None}
    if not operation_matrix:
        operation_matrix = {
            'employee': {'read', 'edit'},
            'breach': {'read', 'edit', 'create'},
            'referential': {'read', 'write'},
            'security': {'read', 'write'},
            'special': {},  # for IT only : batch reset, fakeSSO, etc.
            'nothing': 'void'
        }
    scopes = {}
    for obj_name, ops in operation_matrix.items():
        obj_desc = objects.get(obj_name, '')
        if not ops:
            scopes[obj_name] = obj_desc
            continue
        for op in ops:
            if not entities[obj_name]:
                scopes['{}-{}'.format(op, obj_name)] = describe_scope(op, obj_desc)
                continue
            for entity in entities[obj_name]:
                scopes['{}-{}-{}'.format(op, obj_name, entity)] = describe_scope(op, obj_desc, entity)

    return scopes


central_security.scopes = define_scopes_as_combination(__objects, __entities, __operation_matrix)

central_security.profiles = {
    'Administrator': 'Special maintenance rights for developers and IT supports (includes security)',
    'Breach Case Inputter': 'Able to view and create breach under SG Entities Constraints + Breach Process Owner Constraints (Ivisible to other tables and breach score)',
    'CPLE Culture and Conduct Adminstrator': 'Administrator rights for Culture and Conduct Team',
    'Manager': 'Manager level access',
    'Unit Breach Policy Officer (EMEA)': 'Administrator officer for EMEA',
    'Breach Case Inputter (EMEA)': 'Able to view and create breach under SG Entities Constraints + Breach Process Owner Constraints (Invisible to other tables and breach score) for EMEA',
}

central_security.profiles_to_scopes = {
    'Administrator': ['special', 'read-security', 'write-security'],
    'Manager': ['manager-special'],
    'CPLE Culture and Conduct Administrator': ['read-employee-Region:APAC'],
    'Unit Breach Policy Officer (EMEA)': ['read-employee-Region:EMEA', 'read-breach-Region:EMEA'],
    'Breach Case Inputter (EMEA)': ['read-breach-Region:EMEA'],
    'Staff': ['read-nothing'],
}

# scopes_immutables define the Role table in the database
scopes_immutables = central_security.scopes
