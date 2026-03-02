package com.socgen.pad.obi.web.rest;

import com.socgen.pad.framework.web.rest.interceptor.RSController;
import com.socgen.pad.obi.domain.model.ObaPiType;
import com.socgen.pad.obi.domain.service.ObaPiConsumptionService;
import com.socgen.pad.obi.web.mapper.ConsumptionResponseDtoMapper;
import com.socgen.pad.obi.web.rest.swagger.ApiConsumptionResourceSwagger;
import lombok.AllArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.Optional;

@RSController
@RequestMapping("api/v1/consumptions")
@AllArgsConstructor
@PreAuthorize("hasAnyAuthority('SCOPE_api.personal-account-dealing-oba-pi.read-all')")
public class ApiConsumptionResource implements ApiConsumptionResourceSwagger {

    private ConsumptionResponseDtoMapper dtoMapper;
    private ObaPiConsumptionService service;

    @GetMapping("obas")
    public Object getAllAObaByGgi(@RequestParam Optional<String> ggi) {
        if (ggi.isPresent()) {
            return dtoMapper.toResponseList(service.getAllObaPiByTypeAndGgi(ObaPiType.OBA, ggi.get()));
        }
        return dtoMapper.toResponseList(service.getAllObaPiByType(ObaPiType.OBA));
    }

    @GetMapping("private-investments")
    public Object getAllPiByGgi(@RequestParam Optional<String> ggi) {
        if (ggi.isPresent()) {
            return dtoMapper.toResponseList(service.getAllObaPiByTypeAndGgi(ObaPiType.PI, ggi.get()));
        }
        return dtoMapper.toResponseList(service.getAllObaPiByType(ObaPiType.PI));
    }
}