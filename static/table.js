$(document).ready(
    function () {
        $('#table_id').DataTable(
            {
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