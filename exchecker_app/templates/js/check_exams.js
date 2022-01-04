$(document).ready(function() {
    // First register any plugins
    $.fn.filepond.registerPlugin(FilePondPluginImagePreview,
                                 FilePondPluginImageTransform,
                                 FilePondPluginFileValidateType,
                                 FilePondPluginFileEncode);
    
    // Set server options
    let csrftoken = Cookies.get('csrftoken');
    $.fn.filepond.setOptions({
                server: {
                    process: {
                        url: 'upload_exams/',
                        headers: {'X-CSRFToken': csrftoken},
                        method: 'POST'
                    },
                    fetch: null,
                    revert: null,
                    restore: null,
                    load: null
                }
            });


    // Turn input element into a pond
    $('.my-pond').filepond();

    // Set Spanish languaje
    $('.my-pond').filepond('labelIdle', 'Arrastra y suelta tus ficheros o <span class="filepond--label-action"> súbelos </span>');
    $('.my-pond').filepond('labelFileWaitingForSize', 'Calculando tamaño');
    $('.my-pond').filepond('labelFileLoading', 'Cargando');
    $('.my-pond').filepond('labelFileLoadError', 'Error durante la carga');
    $('.my-pond').filepond('labelTapToCancel', 'Click para cancelar');
    $('.my-pond').filepond('labelButtonRemoveItem', 'Eliminar');
    $('.my-pond').filepond('labelButtonAbortItemLoad', 'Abortar');
    $('.my-pond').filepond('labelButtonRetryItemLoad', 'Reintentar');
    $('.my-pond').filepond('labelFileProcessing', 'Subiendo');
    $('.my-pond').filepond('labelFileProcessingComplete', 'Completado');
    $('.my-pond').filepond('labelTapToUndo', 'Click para cancelar');
    

    // Set properties
    $('.my-pond').filepond('allowMultiple', true);
    $('.my-pond').filepond('required', true);
    $('.my-pond').filepond('maxFiles', 50);

    $('.my-pond').filepond('acceptedFileTypes', ['image/png', 'image/jpeg', 'application/pdf']);

    $("#penalty_personalized").click(function(){
        $("#penalty").removeClass("oculto");
        $('#penalty').attr('required', true);
    });
    $("#penalty_formula").click(function(){
        $("#penalty").addClass("oculto");
        $('#penalty').attr('required', false);
    }); 
    $("#no_penalty").click(function(){
        $("#penalty").addClass("oculto");
        $('#penalty').attr('required', false);
    });

    $("#send_button").click(function() {
        $("#check_modal").modal('show');
    });

});