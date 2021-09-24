define([
  './utilities', './globals',
], (
  { createElement }, { CELL_METADATA, GLOBAL_CONSTANTS },
) => class CellButton {
  constructor(container, defaultState, props, id) {
    /* description of constructor properties
     * {param} container: DOMElement: container where the DOMButtons are held
     * {param} defaultState: STR/BOOL: default state as key of props to take details from by default
     * {param} props: OBJ: object of the following structure:
     *    {
     *      'state1': {
     *        icon: 'icon_path',
     *        func: () => { what_happens_when_pressed },
     *        tooltip: 'button_tooltip_text',
     *      },
     *      'state2': { ...analogically_as_state1 }
     *    }
     * {param} id: STR: unique per cell name of button's "main functionality desc" (eg. "copy" or "edit")
    */
    this.id = id;
    this.container = container;
    this.disabled = false;
    this.defaultState = defaultState;
    this.properStates = [...Object.keys(props)];

    if (this.properStates.length > 2) {
      throw new Error('CellButton structure error: more than two possible states found.');
    }

    this.state = defaultState;
    this.props = props;
    this.currentParameters = {};
    this.img = createElement('img', {});
    this.tooltipTextHolder = createElement('span');
    this.tooltip = createElement('div', { class: 'mstr-tooltip force-hidden' }, [
      createElement('div', { class: 'arrow' }),
      this.tooltipTextHolder,
    ]);

    this.element = createElement('button', {
      role: 'button',
      class: 'mstr-cell-button',
      name: this.id,
      tabIndex: -1,
    }, container, [
      this.img,
      this.tooltip,
    ]);

    this.element.addEventListener('click', () => {
      this.func();
      const newStateOptions = this.properStates.filter((state) => state !== this.state);
      newStateOptions.length && this.setState(newStateOptions[0]);
    });

    this.setState(this.defaultState);

    // workaround for Safari:
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions#Browser_compatibility
    this.setState = this.setState.bind(this);
    this.isProperState = this.isProperState.bind(this);
    this.remove = this.remove.bind(this);
    this.refreshDom = this.refreshDom.bind(this);
    this.showTooltip = this.showTooltip.bind(this);
    this.hideTooltip = this.hideTooltip.bind(this);
    this.disable = this.disable.bind(this);
    this.enable = this.enable.bind(this);
    this.click = this.click.bind(this);

    this.element.addEventListener('mouseenter', this.showTooltip);
    this.element.addEventListener('mouseleave', this.hideTooltip);
  }


  // parameters getters / setters
  get icon() {
    const { ORIGIN, EXTENSION_MAIN_FOLDER } = GLOBAL_CONSTANTS;
    return `${ORIGIN}${EXTENSION_MAIN_FOLDER}/${this.currentParameters.icon}`;
  }

  get func() {
    return this.currentParameters.func;
  }

  get tooltipText() {
    return this.currentParameters.tooltip;
  }


  // methods
  setState(state) {
    if (!this.isProperState(state)) throw new Error('CellButton structure error: cannot recognize a state to set.');
    this.state = state;
    this.currentParameters = { ...this.props[state] };
    this.refreshDom();
  }

  isProperState(state) {
    return this.properStates.includes(state);
  }

  remove() {
    return this.element.remove();
  }

  refreshDom() {
    this.img.setAttribute('src', this.icon);
    this.tooltipTextHolder.textContent = this.tooltipText;
  }

  showTooltip() {
    return this.tooltip.classList.remove('force-hidden');
  }

  hideTooltip() {
    return this.tooltip.classList.add('force-hidden');
  }

  disable() {
    this.disabled = true;
    this.element.classList.add('force-disabled');
  }

  enable() {
    this.disabled = false;
    this.element.classList.remove('force-disabled');
  }

  click() {
    return !this.disabled && this.element.click();
  }


  // static value generators
  static functions(instanceMSTRCell) {
    return {
      'code-copy': async () => {
        // support for all browsers need to be implemented in two ways:
        // https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/Interact_with_the_clipboard
        instanceMSTRCell.engine().applyInstructions();
        const code = instanceMSTRCell.kernel.codeString;

        // navigator query is enabled in browser:
        if (navigator && navigator.permissions && navigator.clipboard) {
          const result = await navigator.permissions.query({ name: 'clipboard-write' });
          const isGrantedStates = ['granted', 'prompt'];
          if (isGrantedStates.includes(result.state)) {
            // app is allowed to put stuff into clipboard:
            navigator.clipboard.writeText(code)
              .catch((err) => console.error('Copy to Clipboard failed! ', err));
            return;
          }
        }

        // navigator is not enabled / there is no "clipboard-write" access:
        const textarea = document.querySelector('#mstr-copy-to-clipboard-object');
        textarea.value = code;
        textarea.select();
        document.execCommand('copy');
        textarea.value = '';
      },
      'code-edit': () => {
        window.showMstrModal() // after opening UI, backendManager is available
          .then(() => {
            // modal is open and backendManager available
            const { backendManager } = window;
            backendManager.requestDataEdit(
              instanceMSTRCell.type,
              instanceMSTRCell.metadata[CELL_METADATA.DATA],
              instanceMSTRCell.index,
            );
          })
          .catch(() => {
            console.error(
              'MSTRIO-py Error: BackendManager is not available. Connection Timeout. Cannot connect to UI',
            );
          });
      },
      'code-hide': () => {
        instanceMSTRCell.engine().setCodeVisible('', instanceMSTRCell.codePrefix);
        instanceMSTRCell.metadataAdd({ [CELL_METADATA.CODE_HIDDEN]: true });
      },
      'code-run': () => {
        instanceMSTRCell.engine().execute();
      },
      'code-show': () => {
        instanceMSTRCell.engine().setCodeVisible(instanceMSTRCell.kernel.codeString, instanceMSTRCell.codePrefix);
        instanceMSTRCell.metadataAdd({ [CELL_METADATA.CODE_HIDDEN]: false });
      },
      'table-hide': () => {
        instanceMSTRCell.hideTable();
      },
      'table-show': () => {
        instanceMSTRCell.showTable();
      },
    };
  }

  static tooltips() {
    return {
      'code-copy': 'Copy Python Code to clipboard',
      'code-edit': 'Edit Data in MicroStrategy for Jupyter',
      'code-hide': 'Hide Python Code',
      'code-run': 'Run',
      'code-show': 'Show Python Code',
      'table-hide': 'Hide Table',
      'table-show': 'Show Table',
    };
  }
});
