package ticketBookingApp.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import ticketBookingApp.entity.Screen;
import ticketBookingApp.service.ScreenService;

import java.util.List;

@Controller
public class SearchController {

    @Autowired
    private ScreenService screenService;

    @GetMapping("/search")
    public String search(@RequestParam("screen") Long screenId, Model model) {
        List<Screen> screens = screenService.searchByScreenId(screenId);
        // Implement search logic based on screenId
        // Pass search results to the view
        model.addAttribute("screens", screens);
        return "search";
    }
}
