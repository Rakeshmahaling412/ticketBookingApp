package sg.breach.user.repository;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import sg.breach.user.entity.UserEntity;

public interface UserRepository extends JpaRepository<UserEntity, Long> {
    Optional<UserEntity> findOneByEmailIgnoreCase(String email);
}
