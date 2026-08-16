package sg.breach.user.repository;

import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import sg.breach.user.entity.RoleEntity;

public interface RoleRepository extends JpaRepository<RoleEntity, Long> {
    List<RoleEntity> findByNameIn(Collection<String> names);
}
