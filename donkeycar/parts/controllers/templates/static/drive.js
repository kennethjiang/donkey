var driveHandler = new function() {
    self = this;

    self.load = function() {
        driveURL = '/api/drive';
        bindings();

        $.get(driveURL, function(data) {
            updateUI(data);
        });
    };

    var postDrive = function() {
        //Send angle and throttle values
        data = JSON.stringify({
            'drive_mode': self.state.drive_mode,
            'recording': self.state.recording,
            'max_throttle': self.state.max_throttle
        });

        $.post(driveURL, data, function(data) {
            updateUI(data);
        });
    };

    var bindings = function() {
        $('#drive-mode button').click(function() {
            self.state.drive_mode = $(this).attr('id');
            postDrive();
        });
        $('#record_button').click(function() {
            self.state.recording = !self.state.recording;
            postDrive();
        });
        $('#max_throttle_select').change(function() {
            self.state.max_throttle = $('#max_throttle_select').val();
            postDrive();
        });
    };

    var updateUI = function(str) {
        self.state = JSON.parse(str);

        $('#drive-mode button').removeClass('btn-primary').addClass('btn-default');
        $('#drive-mode button#'+self.state.drive_mode).addClass('btn-primary').removeClass('btn-default');

        $('#max_throttle_select').val(self.state.max_throttle);

        if (self.state.recording) {
          $('#record_button')
            .html('Stop Recording')
            .removeClass('btn-primary')
            .addClass('btn-warning').end()
        } else {
          $('#record_button')
            .html('Start Recording')
            .removeClass('btn-warning')
            .addClass('btn-primary').end()
        }

    };

}();
