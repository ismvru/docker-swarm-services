$(document).ready(function () {
    $('#table_id').DataTable({
        ajax: '/',
        columns: [
            { data: 'short_id' },
            { data: 'name' },
            { data: 'image' },
            { data: 'tag' },
            { data: 'created' },
            { data: 'created_human' },
            { data: 'updated' },
            { data: 'updated_human' }
        ],
    });
});