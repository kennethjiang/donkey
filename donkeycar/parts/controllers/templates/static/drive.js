var driveHandler = new function() {
    this.load = function() {
        driveURL = '/api/drive';
        bindings();

        $.get(driveURL, function(data) {
            updateUI(data);
        });
    };

    var postDrive = function() {
        var driveMode = $("#drive-mode button.btn-primary").attr('id');

        //Send angle and throttle values
        data = JSON.stringify({
            'drive_mode': driveMode,
            'recording': false,
            'max_throttle': 0.5
        });

        console.log(data);
        $.post(driveURL, data, function(data) {
            updateUI(data);
        });
    };

    var bindings = function() {
        $('#drive-mode button').click(function() {
            $(this).removeClass('btn-default').addClass('btn-primary').parent().siblings().find('button').removeClass('btn-primary').addClass('btn-default');
            postDrive();
        });
    };

    var updateUI = function(str) {
        var data = JSON.parse(str);
        $('#drive-mode button').removeClass('btn-primary').addClass('btn-default');
        $('#drive-mode button#'+data.drive_mode).addClass('btn-primary').removeClass('btn-default');
        $('#max_throttle_select').val(data.max_throttle);
    };

}();
