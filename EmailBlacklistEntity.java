package sg.breach.emailblacklist.enity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table(name = "do_not_send_email_to")
@Getter
@Setter
@NoArgsConstructor
public class EmailBlacklistEntity {

    @Id
    @Column(name = "email", nullable = false, unique = true)
    private String email;

}
