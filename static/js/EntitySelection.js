var selectedEntities = []
var selectedType = null

var entitySelectTable
var documentTable

const entityColors = {
    'PERSON': 'btn btn-primary',
    'ORGANIZATION': 'btn btn-danger',
    'LOCATION': 'btn btn-info',
}

$(document).ready(function() {
  entitySelectTable = $('#entitySelectTable').DataTable({
        "paging": true,
    "serverSide": true,
    "processing": true,
      order: [[ 1, "desc" ]],
    "ajax": {
          url: "entity/api",
      type: "post",
      datatype: "json",
      data: function(d){
            d.type = selectedType
            d.parents = getEntityIds()
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
            defaultContent: "<button type='button' class='btn btn-success'>Add</button>"
        },
        {
            name: 'id',
            visible: false
        }
        ]});

    documentTable = $('#documentTable').DataTable({
        "paging": true,
        "serverSide": true,
        "processing": true,
        "ajax": {
            url: "document/api",
            type: "post",
            datatype: "json",
            order: [[ 1, "desc" ]],
            data: function(d){
                d.parents = getEntityIds()
            return { "args": JSON.stringify(d) };}
        },
        "columnDefs": [
            {
                name: 'file_name',
                orderable: true,
                searchable: false,
                targets: [0]
            },
            {
                name: 'path',
                orderable: true,
                searchable: false,
                targets: [1]
            },
            {
                targets: [2],
                data: null,
                defaultContent: "<button type='button' class='btn btn-info'>View</button>"
            }
        ]});

    $('#entitySelectTable tbody').on( 'click', 'button', function () {
        var row = entitySelectTable.row( $(this).parents('tr') ).data();
        const name = row[0]
        const type = row[2]
        const id = row[3]

        const entity = {id: id, name: name, type: type}

        addEntity(entity)
        addEntityButtons()
    });

    $('#tableButtonGroup button').on('click', function() {
        var thisBtn = $(this);
        var value = thisBtn.val();
        selectedType = value;
        entitySelectTable.draw()
      });

    $('#documentTable tbody').on( 'click', 'button', function () {
        var row = documentTable.row( $(this).parents('tr') ).data();
        const fileName = row[0]
        const path = row[1]
        window.location = `document?file_name=${fileName}&path=${path}`
    });

    if (selectedEntities.length > 0) {
        addEntityButtons()
    }

});

function removeEntity(id) {
    for( var i = 0; i < selectedEntities.length; i++){
       if ( parseInt(selectedEntities[i].id) === parseInt(id)) {
         if (selectedEntities.length == 1) {
             selectedEntities = []
         } else {
             selectedEntities.splice(i, 1)
         }
       }
    }
    $(`#button-${id}`).remove()
    entitySelectTable.draw()
    documentTable.draw()
}


function addEntity(entity) {
    selectedEntities.push(entity);
}

function addEntityButtons() {

    selectedEntities.forEach(function (entity) {
        const className = entityColors[entity.type]

        if ($(`#button-${entity.id}`).length == 0) {
             $('.selected-entities').append(
                `<button type="button" style="margin: 2px" onclick="removeEntity(${entity.id})" id="button-${entity.id}" class="${className}" autocomplete="off"> \
                  ${entity.name} \
                </button>`)
        }
    })

        entitySelectTable.draw()
        documentTable.draw()
}

function getEntityIds() {
    let ids = []
    selectedEntities.forEach(function(entity) {
        ids.push(parseInt(entity.id))
    })
    return ids
}
