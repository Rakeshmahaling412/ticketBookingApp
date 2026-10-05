package sg.breach.emailblacklist.enity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.util.ArrayList;
import java.util.List;
@Entity
@Table(name = "email_history")
@Getter
@Setter
public class EmailHistory {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @Column(name = "email_content")
    private String emailContent;
    @Column(name = "sender")
    private String sender;
    @ElementCollection
    @CollectionTable(name = "email_history_recipients", joinColumns = @JoinColumn(name = "email_history_id"))
    @Column(name = "recipient")
    private List<String> recipients = new ArrayList<>();
    @Column(name = "response_details")
    private String responseDetails;
}
