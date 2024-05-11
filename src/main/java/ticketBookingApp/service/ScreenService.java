package ticketBookingApp.service;

import ticketBookingApp.entity.Screen;

import java.util.List;

public interface ScreenService {

    List<Screen> searchByScreenId(Long screenId);

    List<Screen> getAlScreens();
}
