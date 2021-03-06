var selectedType = null
var topTable


$(document).ready(function() {
  topTable = $('#topTable').DataTable({
        "paging": true,
    "serverSide": true,
    "processing": true,
      order: [[ 1, "desc" ]],
    "ajax": {
          url: "entity/api/pure",
      type: "post",
      datatype: "json",
      data: function(d){
            d.type = selectedType
            d.parents = typeof entities !== 'undefined' ? entities : []
            d.doc_table = true
        return { "args": JSON.stringify(d) };
      }
    }
    ,
    "columnDefs": [
        {
            name: 'name',
            orderable: true,
            searchable: true,
            targets: [0]
        },
        {
            name: 'total',
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
            defaultContent: "<button type='button' class='btn btn-info'>Relationships</button>"
        },
        {
            name: 'id',
            visible: false
        },
        {
            name: 'full_name',
            visible: false
        }

    ]});
  $('#topTable tbody').on( 'click', 'button', function () {
        var row = topTable.row( $(this).parents('tr') ).data();
        const name = row[4]
        const type = row[2]
        const id = row[3]
        window.location = `entity?id=${id}&name=${name}&type=${type}`
    });

  $('#tableButtonGroup button').on('click', function() {
    var thisBtn = $(this);
    var value = thisBtn.val();
    selectedType = value;
    topTable.draw()
  });
});
