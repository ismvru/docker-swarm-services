$(document).ready(
    function () {
        $('#table_id').DataTable(
            {
                paging: false,
                order: [[1, 'asc']],
                dom: 'Bfrtip',
                buttons: [
                    {
                        extend: 'copyHtml5',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'csvHtml5',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'excelHtml5',
                        autoFilter: true,
                        sheetName: 'Exported data',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
                    {
                        extend: 'pdfHtml5',
                        orientation: 'landscape',
                        pageSize: 'A4',
                        download: 'open',
                        exportOptions: {
                            columns: ':visible'
                        }
                    },
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
                    { data: 'replication_mode' },
                    { data: 'replica_count' },
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