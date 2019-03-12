var selectedType = null

$(document).ready(function() {
  const resolveTable = $('#matchesTable').DataTable({
        "paging": true,
    "serverSide": true,
    "processing": true,
      order: [[ 1, "desc" ]],
    "ajax": {
          url: "resolve/api",
      type: "post",
      datatype: "json",
      data: function(d){
            d.type = selectedType
        return { "args": JSON.stringify(d) };
      }
    }
    ,
    "columnDefs": [
        {
            name: 'name',
            orderable: false,
            searchable: false,
            targets: [0]
        },
        {
            name: 'count',
            orderable: true,
            searchable: false,
            targets: [1]
        },
        {
            name: 'type',
            orderable: false,
            searchable: false,
            targets: [2]
        },
        {
            targets: [3],
            data: null,
            defaultContent: "<input type='text' id='row-1' name='row-1' value=''>"
        },
        {
            targets: [4],
            data: null,
            defaultContent: "<button type='button' class='btn btn-primary'>Merge</button>"
        },
        {
            name: 'id',
            visible: false
        }

    ]});

  $('#matchesTable tbody').on( 'click', 'button', function () {
    var row = resolveTable.row( $(this).parents('tr') ).data();
    const values = resolveTable.$('input')
    var tr = $(this).closest("tr");
    var rowindex = tr.index();
    const type = row[2]
    const newName = values[rowindex].value
    const id = row[3]

    if (newName != '') {
        const data = { cluster: { id: id, new_name: newName, type: type }}
        var saveData = $.ajax({
            type: "POST",
            url: "resolve/api/merge",
            contentType: "application/json",
            dataType: "json",
            async: false,
            data: JSON.stringify(data),
            success: function () {
                alert("Merge Successful");
            }
        })
        resolveTable.draw()
    } else {
        alert('Please enter a new name.')
    }})

    $('#tableButtonGroup button').on('click', function() {
        var thisBtn = $(this);
        var value = thisBtn.val();
        selectedType = value;
        resolveTable.draw()
      });
});
