define(['material', 'cards/node', 'jquery'], function (mdc, Node) {
  class StartNewSessionNode extends Node {
    editBody () {
      let body = ''

      body += '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'
      body += '<div class="mdc-select mdc-select--outlined" id="' + this.cardId + '_select_script" style="width: 100%">'
      body += '  <div class="mdc-select__anchor">'
      body += '    <span class="mdc-notched-outline">'
      body += '      <span class="mdc-notched-outline__leading"></span>'
      body += '      <span class="mdc-notched-outline__notch">'
      body += '        <span id="outlined-select-label" class="mdc-floating-label">Start New Session</span>'
      body += '      </span>'
      body += '      <span class="mdc-notched-outline__trailing"></span>'
      body += '    </span>'
      body += '    <span class="mdc-select__selected-text-container">'
      body += '      <span class="mdc-select__selected-text"></span>'
      body += '    </span>'
      body += '    <span class="mdc-select__dropdown-icon">'
      body += '      <svg class="mdc-select__dropdown-icon-graphic" viewBox="7 10 10 5" focusable="false">'
      body += '        <polygon class="mdc-select__dropdown-icon-inactive" stroke="none" fill-rule="evenodd" points="7 10 12 15 17 10"></polygon>'
      body += '        <polygon class="mdc-select__dropdown-icon-active" stroke="none" fill-rule="evenodd" points="7 15 12 10 17 15"></polygon>'
      body += '      </svg>'
      body += '    </span>'
      body += '  </div>'
      body += '  <div class="mdc-select__menu mdc-menu mdc-menu-surface mdc-menu-surface--fullwidth">'
      body += '    <ul class="mdc-list" role="listbox" aria-label=Embedded Dialog" id="' + this.cardId + '_dialog_list">'
      body += '    </ul>'
      body += '  </div>'
      body += '</div>'
      body += '</div>'

      return body
    }

    viewBody () {
      let summary = '<div class="mdc-typography--body1" style="margin: 16px;">Start a new session with dialog:</div>'

      summary += '<div class="mdc-typography--body1" style="margin: 16px;">' + this.definition.script_id + '</div>'

      return summary
    }

    initialize () {
      super.initialize()

      const me = this

      $.get('/builder/active-dialogs.json', function (data) {
        $.each(data, function (index, value) {
          let itemHtml = '<li class="mdc-list-item" aria-selected="false" data-value="' + value.id + '" role="option">'
          itemHtml += '  <span class="mdc-list-item__ripple"></span>'
          itemHtml += '  <span class="mdc-list-item__text">' + value.name + '</span>'
          itemHtml += '</li>'

          $('#' + me.cardId + '_dialog_list').append(itemHtml)
        })

        const scriptField = mdc.select.MDCSelect.attachTo(document.getElementById(me.cardId + '_select_script'))

        scriptField.listen('MDCSelect:change', () => {
          const originalId = me.definition.script_id

          me.definition.script_id = scriptField.value

          if (originalId !== me.definition.script_id) {
            me.dialog.markChanged(me.id)
          }
        })

        if (me.definition.script_id !== undefined) {
          scriptField.value = '' + me.definition.script_id
        }
      })
    }

    destinationNodes (dialog) {
      return []
    }

    updateReferences (oldId, newId) {
      if (this.definition.script_id === oldId) {
        this.definition.script_id = newId
      }
    }

    cardType () {
      return 'Start New Session'
    }

    static cardName () {
      return 'Start New Session'
    }

    static createCard (cardName) {
      const id = Node.uuidv4()

      const card = {
        type: 'start-new-session',
        name: cardName,
        id
      }

      return card
    }
  }

  Node.registerCard('start-new-session', StartNewSessionNode)

  return StartNewSessionNode
})
