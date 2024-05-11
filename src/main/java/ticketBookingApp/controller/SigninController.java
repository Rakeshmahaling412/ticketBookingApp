package ticketBookingApp.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import ticketBookingApp.service.UserService;

@Controller
public class SigninController {

    @Autowired
    private UserService userService;

    @GetMapping("/signin")
    public String showSigninForm() {
        return "signin";
    }

    @PostMapping("/signin")
    public String signin(@RequestParam("username") String username,
                         @RequestParam("password") String password) {
        if (userService.authenticate(username, password)) {
            return "redirect:/";
        } else {
            return "redirect:/signin?error";
        }
    }
}
