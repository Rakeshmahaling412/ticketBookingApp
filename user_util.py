from enum import Enum

from flask_login import current_user

from cpla_flask_admin.util.admin_view_secured import central_security
from cpla_flask_admin.util.custom_exceptions import NoValidSGIAMProfileException


class EntitySeparator(Enum):
    ENTITY = '-'
    BPO = '-BPO:'
    REGION = '-Region:'


def get_entity_from_constraints(access_type: str, entity_separator: str) -> list:
    """
    function to get either countries/BU entities under permission (access_type)
    :param access_type: {'read', 'write', 'write-feed', 'configure-feed'}
    :param entity_separator: The separator to distinguish business units or countries
    :param use_mapping: Boolean to indicate the extraction of mapped entities from central_security.entities_mappings
    :return: list of entities
    """
    # if access_type not in {'read-data', 'write-data', 'write-feed', 'configure-feed'}:
    #    raise ValueError("Access type must be read/write/feed-control")

    entities = []
    # Collecting country codes for applied country constraints: view C2 news + edit c0/c1/c2 news under the country
    # write-feed-BU:FCU / write-feed-HKG -> ['FCU'] for BU / ['HKG'] for countries
    # Get the mapping if entity as a key exists in the dictionary
    for role in current_user.roles:
        if access_type + entity_separator in str(role) and ':' not in str(role).split(entity_separator)[-1]:
            raw_entity = str(role).split(entity_separator)[-1]
            mapped_entities = central_security.entities_mappings.get(raw_entity, [raw_entity])
            entities.extend(mapped_entities)

    return entities


def get_user_profile_name():
    roles = set([str(role) for role in current_user.roles])
    if 'special' in roles:
        return 'Administrator'
    elif any(['manager-special' in role for role in roles]):
        return 'Manager'
    elif any(['read-employee-Region:EMEA' in role for role in roles]):
        return 'Unit Breach Policy Officer (EMEA)'
    elif any(['read-breach-Region:EMEA' in role for role in roles]):
        return 'Breach Case Inputter (EMEA)'

    raise NoValidSGIAMProfileException

def can_user_view_breach(create_by_igg) -> bool:
    if get_user_profile_name() == 'Breach Case Inputter (EMEA)':
        if current_user.igg == create_by_igg:
            return True
        return False
    return True

def is_restricted():
    return get_user_profile_name() in {'Breach Case Inputter', 'Staff', 'Manager'}


def get_user_breach_readable_entities():
    return get_entity_from_constraints('read-breach', EntitySeparator.ENTITY.value)

def get_user_breach_readable_regions():
    return get_entity_from_constraints('read-breach', EntitySeparator.REGION.value)


def get_user_breach_readable_bpos():
    return get_entity_from_constraints('read-breach', EntitySeparator.BPO.value)


def get_user_breach_editable_entities():
    return get_entity_from_constraints('edit-breach', EntitySeparator.ENTITY.value)


def get_user_breach_editable_bpos():
    return get_entity_from_constraints('edit-breach', EntitySeparator.BPO.value)


def get_user_breach_creatable_entities():
    return get_entity_from_constraints('create-breach', EntitySeparator.ENTITY.value)


def get_user_breach_creatable_bpos():
    return get_entity_from_constraints('create-breach', EntitySeparator.BPO.value)


def get_user_employee_readable_entities():
    return get_entity_from_constraints('read-employee', EntitySeparator.ENTITY.value)
