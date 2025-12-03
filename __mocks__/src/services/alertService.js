// __mocks__/src/services/alertService.js

class AlertService {
  constructor() {
    this.sendSlackAlert = jest.fn();
  }
}

export default AlertService;
