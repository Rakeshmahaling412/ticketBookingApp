import { Role } from '../../../routes/user-management/shared/model/role';
import { RoleConstants } from '../../constants/role.enum';
import { RoleConfiguration } from './role-configuration.model';
import {Country} from "../feature-country/country.constants";

const accountAdminRoute = 'disclosures/accounts/admin';
const tradeApprovalAdminRoute = 'disclosures/trade-approvals/admin';
const userManagementRoute = 'user-management/users';
const todoManager = 'disclosures/todo/manager';
const todoEmployee = 'disclosures/todo/employee';
const todoAdmin = 'disclosures/todo/admin';
const dashboardRoute = 'disclosures/dashboard/admin';
const obaAdminRoute = 'disclosures/oba/admin';
const tradeApprovalEmployeeRoute = 'disclosures/trade-approvals';


const supplementalApproverRoute = 'disclosures/oba/admin';

const COMMON_CONFIGURATION: RoleConfiguration[] = [
    {key: RoleConstants.SupplementalApprover, defaultRoute: supplementalApproverRoute, priority: 3},
    {key: RoleConstants.SuperAdmin, defaultRoute: userManagementRoute, priority: 4},
    {key: RoleConstants.DesignatedSupervisor, defaultRoute: todoManager, priority: 5, pathKeyWord: 'manager'},
    {key: RoleConstants.Manager, defaultRoute: todoManager, priority: 6, pathKeyWord: 'manager'},
    {key: RoleConstants.TradeReviewManager, defaultRoute: todoManager, priority: 8, pathKeyWord: 'trade-review-manager'},
    {key: RoleConstants.Reconciliation, defaultRoute: accountAdminRoute, priority: 9},
    {key: RoleConstants.ITSupport, defaultRoute: accountAdminRoute, priority: 10},
    {key: RoleConstants.IdentityAccessManagement, defaultRoute: userManagementRoute, priority: 11},
    {key: RoleConstants.Audit, defaultRoute: accountAdminRoute, priority: 12},
    {key: RoleConstants.CmsAdmin, defaultRoute: accountAdminRoute, priority: 13}
];

const HK_GB_CONFIGURATION: RoleConfiguration[] = [
    {key: RoleConstants.ControlRoom, defaultRoute: todoAdmin, priority: 1},
    {key: RoleConstants.ComplianceAdmin, defaultRoute: accountAdminRoute, priority: 2},
    {key: RoleConstants.ObaHumnReadOnly, defaultRoute: obaAdminRoute, priority: 3},
    ...COMMON_CONFIGURATION
];
const US_CONFIGURATION: RoleConfiguration[] = [
    {key: RoleConstants.ControlRoom, defaultRoute: tradeApprovalAdminRoute, priority: 1},
    {key: RoleConstants.ComplianceAdmin, defaultRoute: dashboardRoute, priority: 2},
    ...COMMON_CONFIGURATION
];

function findConfigurationByCountry(country: string): RoleConfiguration[] {
    const configs = isAmerRegion(country) ? US_CONFIGURATION : HK_GB_CONFIGURATION;
    configs.push(employeeConfiguration(country));
    return configs;
}

function isAmerRegion(country: string){
    return country === Country.CA || country === Country.US;
}

function employeeConfiguration(country: string): RoleConfiguration {
    return  {  key: RoleConstants.Employee,
               defaultRoute: ['HK', 'US', 'CA'].includes(country) ? todoEmployee: tradeApprovalEmployeeRoute,
               priority: 7,
               pathKeyWord: 'employee'
            };
}


export function findConfigurationByKey(key: string, country: string): RoleConfiguration {
    return findConfigurationByCountry(country).find(config => config.key === key);
}

export function findConfigurationForDirectAccessByPath(pathName: string, country: string): RoleConfiguration[] {
    return findConfigurationByCountry(country).filter(config => pathName.includes(config.pathKeyWord));
}

export function compare(role1: Role, role2: Role, country) {
    const role1Configuration = findConfigurationByKey(role1.keyName, country);
    const role2Configuration = findConfigurationByKey(role2.keyName, country);
    if (role1Configuration && role2Configuration) {
        if (role1Configuration.priority && role2Configuration.priority) {
            return role1Configuration.priority >= role2Configuration.priority ? 1 : -1;
        } else {
            return role1Configuration.priority ? - 1: 1;
        }
    } else {
        return role1Configuration ? -1 : 1;
    }
}
