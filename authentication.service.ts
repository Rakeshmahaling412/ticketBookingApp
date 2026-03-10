import {HttpClient, HttpHeaders} from '@angular/common/http';
import {Injectable} from '@angular/core';
import {NgxPermissionsService, NgxRolesService} from 'ngx-permissions';
import {Subject} from 'rxjs';
import {map} from 'rxjs/operators';

import {environment} from '../../../../environments/environment';
import {ISgwtConnectElement} from '../../../../main';
import {Feature} from '../../../routes/user-management/shared/model/feature';
import {Role} from '../../../routes/user-management/shared/model/role';
import {UserModel} from '../../../routes/user-management/shared/model/user.model';
import {UserService} from '../../../routes/user-management/shared/services/user.service';
import {LocalStorageUtils} from './local-storage.utils';
import {UserRoleUtils} from './user-role-utils';
import {Router} from '@angular/router';
import {Country} from '../feature-country/country.constants';
import {RoleConstants} from '../../constants/role.enum';

const wrapper = document.querySelector('sgwt-connect') as ISgwtConnectElement;

@Injectable()
export class AuthenticationService {

    private readonly USER_MANAGEMENT_URL = environment.USER_MANAGEMENT_API_URL;

    sgwtConnect = wrapper.sgwtConnect;
    readonly roleSubject: Subject<Role>;
    private isValidUser: boolean;

    constructor(private readonly userService: UserService,
                private readonly permissionsService: NgxPermissionsService,
                private readonly rolesService: NgxRolesService,
                private readonly router: Router,
                private readonly http: HttpClient) {
        this.roleSubject = new Subject<Role>();
    }

    init(): Promise<boolean> {
        return new Promise<boolean>((resolve, reject) => {
            const url = `${this.USER_MANAGEMENT_URL}users/current`;
            const httpHeaders = new HttpHeaders({
                'Authorization': this.sgwtConnect.getAuthorizationHeader(),
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            });
            const options = {headers: httpHeaders};
            this.http.get(url, options).pipe(
                map(res => res['data'])
            ).subscribe((connectedUser: UserModel) => {
                const activeRoleTmp =  UserRoleUtils.getActiveRole(connectedUser.roles, connectedUser.country);
                try {
                    this.setActiveRole(connectedUser, activeRoleTmp);
                } catch (e) {
                    if (activeRoleTmp === undefined) {
                        this.router.navigate(['page-blank']);
                    }
                }
                resolve(true);
            });
        });
    }

    setValidConnectedUser(connectedUser: UserModel): void {
        this.isValidUser = connectedUser.activatedRole !== undefined;
    }
    get isConnectedUserValid(): boolean {
        return this.isValidUser;
    }

    setActiveRole(connectedUser: UserModel, activeRole: Role): void {
        connectedUser.activatedRole = activeRole;
        this.setValidConnectedUser(connectedUser);
        connectedUser.features = activeRole.features.map((feature: Feature) => feature.keyName);
        for (const role of connectedUser.roles) {
            this.rolesService.addRole(role.keyName, () => true);
        }
        this.permissionsService.loadPermissions(connectedUser.features);
        LocalStorageUtils.storeUser(connectedUser);
        this.roleSubject.next(activeRole);
    }

    currentUser(): UserModel {
        return LocalStorageUtils.getStoredUser();
    }

    get activeRole(): string {
        return this.currentUser().activatedRole.keyName;
    }

    getName(): string {
        const currentUser = this.currentUser();
        return `${currentUser.firstName} ${currentUser.lastName}`;
    }

    getPerimeterCountries() {
        const user = this.currentUser();
        return user.perimeter ? user.perimeter.grantCountries : [user.country];
    }

    hasFeatures(features: string[]): boolean {
        return this.currentUser().features.some((feature: string) => features.includes(feature));
    }

    hasFeaturesByGgi(ggi: string, features: string[]): Promise<boolean> {
        return new Promise(resolve => {
            this.userService.getUserFeaturesByGgi(ggi).subscribe(userFeatures => {
                    const featuresKeys = Array.from(userFeatures.map(feature => feature.keyName));
                    const hasFeatures = featuresKeys.some((feature: string) => features.includes(feature));
                    resolve(hasFeatures);
                },
                err => resolve(false)
            );
        });
    }

    isAmerRegion(){
        return this.currentUser()?.country === Country.CA || this.currentUser()?.country === Country.US;
    }

    isCountryUS(){
        return this.currentUser()?.country === Country.US;
    }

    isCountryCA(){
        return this.currentUser()?.country === Country.CA;
    }

    isCountryBR(){
        return this.currentUser()?.country === Country.BR;
    }
    isCountryFR(){
        return this.currentUser()?.country === Country.FR;
    }
    isCountryGB(){
        return this.currentUser()?.country === Country.GB;
    }

    canViewDataOfCAJVEMployees(recordLegalEntityId){
        return  this.isCountryCA() || (recordLegalEntityId === '0000020592' && this.isCountryUS() && (this.currentUser().activatedRole.keyName === RoleConstants.ComplianceAdmin || this.currentUser().activatedRole.keyName === RoleConstants.ControlRoom));
    }

    canViewCanadaData(recordCountry, recordLegalEntityId){
        if(recordCountry === Country.CA){
            return this.canViewDataOfCAJVEMployees(recordLegalEntityId);
        }
        return true;
    }

    isSEACountry(){
        return  [Country.SG,Country.MY,Country.ID,Country.VN].indexOf(this.currentUser().country) !== -1;
    }

    getControlRoomUserNames() {
        const countries = this.getPerimeterCountries();
        return this.userService.getControlRoomUsers(countries);
    }
}
