$(document).ready(
    function () {
        $('#table_id').DataTable(
            {
                dom: 'Bfrtip',
                buttons: [
                    'copyHtml5', 'csvHtml5', 'excelHtml5', 'pdfHtml5',
                    {
                        extend: 'print',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'colvis',
                        collectionLayout: 'fixed columns',
                        collectionTitle: 'Column visibility control'
                    }
                ],
                ajax: '/ajax',
                columns: [
                    { data: 'short_id' },
                    { data: 'name' },
                    { data: 'stack' },
                    { data: 'image' },
                    { data: 'tag' },
                    { data: 'tasks_count' },
                    { data: 'tasks_running' },
                    { data: 'tasks_shutdown' },
                    { data: 'created' },
                    { data: 'created_human' },
                    { data: 'updated' },
                    { data: 'updated_human' }
                ],
            }
        );
    }
);