'use strict'

let progress_template_interval = "";

function get_progress_template(){
	let csrftoken = Cookies.get('csrftoken');
	let request = new Request(
		"/get_progress_template/",
		{headers: {'X-CSRFToken': csrftoken}}
	);
	let formData = new FormData();
	
	fetch(request, {
		method: 'POST',
		mode: 'same-origin',  // Do not send CSRF token to another domain.
		body: formData
	}).then(function(result) {
		result.json().then(data => {
			if (data === true){
                // The template get process is finished
				$("#getTemplateModal").modal('hide');
				clearInterval(progress_template_interval);
			}
		});
	});
}

$(document).ready(function() {
    // Just show modal when all required inputs are filled
    $("#send_button").click(function() {
        if(($("#school_name").val().length!==0) &&
           ($("#n_questions").val().length!==0) &&
           ($("#n_responses").val().length!==0)) {

			if(!($('#template_name_check').prop('checked')) ||
			  (($('#template_name_check').prop('checked')) &&
			   ($("#template_name").val().length!==0))) {

				progress_template_interval = window.setInterval(get_progress_template, 1000);
            	$("#getTemplateModal").modal('show');
			}
        }
    });

	$("#template_name_check").click(function(){
        if( $('#template_name_check').prop('checked') ) {
			$("#template_name").removeClass("oculto");
        	$('#template_name').attr('required', true);
		}else{
			$("#template_name").addClass("oculto");
        	$('#template_name').attr('required', false);
		}
    });
});