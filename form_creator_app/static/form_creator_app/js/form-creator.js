$(document).ready(backupUnboundFormsetItems)

// Remove select field's options on field type change.
$(document).on('change', 'select', e => {
    let typeField = $(e.target)
    let choiceSet = typeField.closest('.form-creator__field-item')
        .find('.form-creator__field-choices')
    if (typeField.val() == 'select') {
        choiceSet.show()
    } else {
        choiceSet.hide()
        let choiceFields = choiceSet.find('.form-creator__choice-item')
        choiceFields.first().find('[type="text"]').val('')
        choiceFields.slice(1).remove()
    }
})

let unboundField
let unboundChoice

// When the page is ready, backups empty fieldset forms.
// If form is re-rendered fields may contain values -> clear.
function backupUnboundFormsetItems() {
    unboundField = $('.form-creator__field-item:first').clone(true)
    unboundChoice = $('.form-creator__choice-item:first').clone(true)
    resetItemValues(unboundField)
    resetItemValues(unboundChoice)
}

function resetItemValues(item) {
    item.find('p > input:not([type="hidden"])')
        .val('')
        .prop('checked', false)
    item.find('select option').prop('selected', false)
}

// Increments formset form counter.
function incFormCounter(formsetPrefix) {
    let counter = $(`#id_${formsetPrefix}-TOTAL_FORMS`)
    let value = parseInt(counter.val()) + 1
    counter.val(value)
    return value
}

// Decrements formset form counter.
function decFormCounter(formsetPrefix) {
    let counter = $(`#id_${formsetPrefix}-TOTAL_FORMS`)
    let value = parseInt(counter.val()) - 1
    counter.val(value)
    return value
}


function setFormCounter(formsetPrefix, value) {
    let counter = $(`#id_${formsetPrefix}-TOTAL_FORMS`)
    counter.val(value)
    return value
}

// Removes index from formset prefix.
// some_prefix_5 -> some_prefix
function stripFormsetPrefixIdx(prefix) {
    let sepIndices = [...prefix.matchAll(new RegExp('_', 'gi'))]
        .map(m => m.index)
    if (sepIndices.length > 1) {
        return prefix.slice(0, sepIndices.pop())
    }
    return prefix
}

// TODO: Fix indices are assigned incorrectly.
// Updates indices in the names and ids of a cloned form.
function updateFormIdx(form, formsetPrefix, newIdx) {
    formsetPrefix = stripFormsetPrefixIdx(formsetPrefix)

    let formsetPrefixes = new Set()
    formsetPrefixes.add(formsetPrefix)

    let nestedFormsets = form.find('[id$="TOTAL_FORMS"]')
    for (let formset of nestedFormsets) {
        let prefix = /id_(.*)_\d+/.exec($(formset).attr('id').split('-')[0])[1]
        formsetPrefixes.add(prefix)
    }

    for (let prefix of formsetPrefixes) {
        let pattern = RegExp(`(${prefix}[-_]*)\\d*`)
        let value = `$1${newIdx}`

        form.find(`[id^="id_${prefix}"],label[for]`).each(function () {
            let elem = $(this)
            if (elem.prop('tagName') == 'LABEL') {
                let forValue = elem.attr('for').replace(pattern, value)
                elem.attr({'for': forValue})
            } else {
                let name = elem.attr('name').replace(pattern, value)
                let id = `id_${name}`
                elem.attr({name, id})
            }
        })
    }
}

// Determines the position where to put new formset item.
function addFormsetItem(item, formsetPrefix) {
    let itemClass = item.attr('class')
    let lastItem = $(`[id^="id_${formsetPrefix}"`).first()
        .siblings('fieldset')
        .find(`[class="${itemClass}"]:last`)

    lastItem.after(item)
}

// Returns prefix for the formset button of which was clicked.
function getFormsetPrefix(target) {
    return target.closest('fieldset')
        .siblings('[name$="TOTAL_FORMS"]')
        .attr('name')
        .split('-')[0]
}

// Handles addition of a new item to the formset.
function handleFieldAddition(e, form) {
    form = form.clone(true)

    let target = $(e.target)
    let formsetPrefix = getFormsetPrefix(target)
    let newIdx = incFormCounter(formsetPrefix) - 1
    updateFormIdx(form, formsetPrefix, newIdx)
    addFormsetItem(form, formsetPrefix)
}

$(document).on('click', '.form-creator', e => {
    let target = $(e.target)
    let isAddField = target.is('[class*="form-creator__add-field-btn"]')
    let isAddOpt = target.is('[class*="form-creator__add-option-btn"]')

    if (!(isAddField || isAddOpt)) {
        return true
    } else if (isAddField) {
        addField()
    } else if (isAddOpt) {
        addChoice(target)
    }
    return false
})

function addField() {
    let lastField = $('[class*="form-creator__field-item"]:last')
    let newField = lastField.clone(true)

    let formsetPrefix = getFormsetPrefix(lastField)
    let fieldCount = incFormCounter(formsetPrefix)

    let choices = newField.find('[class*="form-creator__choice-item"]')
    choices.slice(1).remove()
    let choiceFormsetPrefix = getFormsetPrefix(choices)
    newField.find('[name$="TOTAL_FORMS"]').val(1)

    let prefixes = [formsetPrefix, stripFormsetPrefixIdx(choiceFormsetPrefix)]
    for (let prefix of prefixes) {
        updateFieldIndices(newField, prefix, fieldCount - 1)
    }

    resetItemValues(newField)
    lastField.after(newField)
}


function addChoice(target) {
    let lastField = target.closest('fieldset')
        .find('[class*="form-creator__choice-item"]:last')
    let newField = lastField.clone(true)

    let formsetPrefix = getFormsetPrefix(lastField)
    let fieldCount = incFormCounter(formsetPrefix)

    updateFieldIndices(newField, formsetPrefix, fieldCount - 1)

    resetItemValues(newField)
    lastField.after(newField)
}


function updateFieldIndices(field, prefix, newIdx) {
    let pattern = RegExp(`(${prefix}[-_])\\d*`)
    let value = `$1${newIdx}`

    field.find(`[id^="id_${prefix}"],label[for]`).each(function () {
        let elem = $(this)
        if (elem.prop('tagName') == 'LABEL') {
            let forValue = elem.attr('for').replace(pattern, value)
            elem.attr({'for': forValue})
        } else {
            let name = elem.attr('name').replace(pattern, value)
            let id = `id_${name}`
            elem.attr({name, id})
        }
    })
}
