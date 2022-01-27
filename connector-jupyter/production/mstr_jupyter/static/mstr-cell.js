define([
  'jquery', // default browser engines
  'notebook/js/codecell', 'notebook/js/cell', 'notebook/js/outputarea', 'notebook/js/celltoolbar', // notebook js
  'codemirror/lib/codemirror', // other js
  './utilities', './cell-button', './globals', // custom files
], (
  $,
  { CodeCell }, { Cell }, { OutputArea }, { CellToolbar },
  CodeMirror,
  Utilities, CellButton, Globals,
) => { // NOSONAR (Too many params: need to stay as this is the way to implement `define()`)
  // not in class structure due to Jupyter CodeCell implementation we need to use
  const { createElement, flagImportExport, XOR } = Utilities;
  const { CELL_METADATA } = Globals;

  const generatePrefix = (cellType, cubeName, cubePath, timeStamp) => `
# ${
  cellType === 'import'
    ? 'Import from MicroStrategy'
    : `Export/${cellType === 'update' ? 'Update' : 'Create'} Cube in MicroStrategy` // NOSONAR
}
# Cell Creation Date: ${Utilities.formatDateToUS(timeStamp)}
# Object Name: ${cubeName}
# ${cubePath}
  `.trim();


  // key event handlers on cells directly
  const keyDownHandler = (event, cell) => {
    const { key: _key, shiftKey, ctrlKey, metaKey, target } = event;
    const key = _key.toLowerCase();
    const keysToLock = [
      // eslint-disable-next-line max-len
      // from Jup GitHub: https://github.com/jupyter/notebook/blob/db46c594bbbac45e0fcaaa91abe4778b89a4200a/notebook/static/notebook/js/keyboardmanager.js#L126
      'm', // change cell type: markdown
      'r', // change cell type: raw
      'y', // change cell type: code (is already "modified code",
      //                        should not allow Jup default behaviour)
      '1', '2', '3', '4', '5', '6', // change cell type: header
    ];
    // stop default Jupyter event for keysToLock
    // & for input fields, stop event
    if (
      (['input', 'textfield'].includes(target.nodeName.toLowerCase()))
      || (!shiftKey && !ctrlKey && !metaKey && keysToLock.includes(key))
    ) {
      event.stopPropagation();
      return;
    }

    // === NEW KEYBOARD SHORTCUTS ===
    const buttonClick = (buttonId) => {
      event.stopPropagation();
      cell.buttons[buttonId] && cell.buttons[buttonId].click();
    };

    // SHIFT+Y: show/hide code
    if (shiftKey && !ctrlKey && !metaKey && key === 'y') {
      buttonClick('code');
      return;
    }

    // SHIFT+CTRL/CMD+O: show/hide output table (O - letter, not zero)
    if (cell.type === 'import' && shiftKey && XOR(ctrlKey, metaKey) && key === 'o') {
      buttonClick('table');
      return;
    }

    // SHIFT+CTRL/CMD+C: copy code
    if (shiftKey && XOR(ctrlKey, metaKey) && key === 'c') {
      buttonClick('copy');
      return;
    }

    // SHIFT+E: edit in UI
    if (shiftKey && !ctrlKey && !metaKey && key === 'e') {
      buttonClick('edit');
      // return; // uncomment when another shortcut is added below
    }
  };


  // === custom engine for CodeCell constructor (properties and methods) ===
  const MSTRCell = function (cellKernel, cellOptions, recreationDetails = {}) {
    this.recreationDetails = recreationDetails;
    this.buttonsFunctions = CellButton.functions(this);
    this.buttonsTooltips = CellButton.tooltips();
    this.type = cellOptions.type;
    this.engine = cellOptions.engine;
    this.outputTable = null;
    this.isRunning = false;

    // props before this line will be overwritten if CodeCell applies them by default
    // but put them before if they might be required inside CodeCell.call() or new MSTRCell()
    CodeCell.call(this, cellKernel, cellOptions);

    this.prepAfterCreation(cellOptions.index);
  };

  // [cannot shorthand this and the following due to the way prototype inheritance works]
  MSTRCell.prototype = Object.create(CodeCell.prototype);

  // getters / setters
  Object.defineProperty(MSTRCell.prototype, 'index', {
    get: function index() { return this.engine().notebook.get_selected_index(); },
  });
  // ---

  MSTRCell.prototype.prepAfterCreation = function (index) { // fires right after instance is created
    this.set_input_prompt();
    if (!this.recreationDetails[CELL_METADATA.IS_MSTR]) {
      let selectedAuthDetails = this.engine().kernel.authenticationDetails;
      selectedAuthDetails = {
        url: selectedAuthDetails.url,
      };
      const data = {
        authenticationDetails: selectedAuthDetails,
        dataframeDetails: this.engine().kernel.dataframeDetails,
        otherDetails: this.engine().kernel.otherDetails,
      };
      this.metadataAdd({
        [CELL_METADATA.IS_MSTR]: true,
        [CELL_METADATA.TYPE]: this.type,
        [CELL_METADATA.DATA]: data,
        [CELL_METADATA.CREATED_DATE]: this.creationDate.toString(),
        [CELL_METADATA.CODE_HIDDEN]: true,
        [CELL_METADATA.TABLE_HIDDEN]: false,
      });
    } else {
      this.metadataAdd(this.recreationDetails);
    }
    if (!this.notebook._insert_element_at_index(this.element, index)) return;
    this.render();
    this.refresh();
    this.element[0].scrollIntoView(true);
  };


  MSTRCell.prototype.create_element = function (...args) { // responsible for DOM manipulation when creating the cell
    // apply default general Cell engine first
    Cell.prototype.create_element.apply(this, args);

    // declare dom elements
    const cellToolbar = new CellToolbar({
      cell: this,
      notebook: this.notebook,
    });
    const buttonsContainer = createElement('div', { class: 'mstr-buttons-container' });

    const inputAreaFunctional = createElement('div', { class: 'force-hidden' });
    const inputAreaVisible = createElement('div', { class: 'input_area visible' }, [
      buttonsContainer,
    ]);

    const input = createElement('div', { class: 'input' }, [
      createElement('div', { class: 'prompt_container' }, [
        createElement('div', { class: 'prompt input_prompt' }),
      ]),
      createElement('div', { class: 'inner_cell' }, [
        cellToolbar.element[0],
        inputAreaFunctional,
        inputAreaVisible,
      ]),
    ]);
    const output = createElement('div');

    const cell = createElement('div', { class: 'cell code_cell', tabindex: 2 }, [
      input,
      output,
    ]);


    // reference: https://codemirror.net/doc/manual.html#config
    const optionsForCustomInputArea = {
      readOnly: true,
      theme: 'ipython',
      indentUnit: 4,
      mode: { name: 'ipython', version: 3 },
      lineWiseCopyCut: false,
      dragDrop: false,
      cursorBlinkRate: -1, // hide cursor
    };


    // update class properties
    // [DOM elements need to be in jQuery format ;(]
    this.celltoolbar = cellToolbar;
    this.element = $(cell);
    this.input = $(input);
    this.code_mirror = new CodeMirror(inputAreaFunctional, this._options.cm_config);
    this.output_area = new OutputArea({
      config: this.config,
      selector: $(output),
      prompt_area: true,
      events: this.events,
      keyboard_manager: this.keyboard_manager,
    });

    // --- custom properties, non-existent in original CodeCell
    // cannot shorhand this as: new Date() != new Date(undefined OR false)
    this.creationDate = this.recreationDetails[CELL_METADATA.CREATED_DATE]
      ? new Date(this.recreationDetails[CELL_METADATA.CREATED_DATE])
      : new Date();
    const {
      dataframeDetails: {
        datasetName = '',
        name: itemName = '',
        path: itemPath = [],
      },
      otherDetails: { saveAsName = '' },
    } = this.engine().kernel;
    this.codePrefix = generatePrefix(
      this.type,
      itemName || (saveAsName || (datasetName || '-')),
      itemPath.join('/'),
      this.creationDate,
    );
    this.customInputArea = new CodeMirror(inputAreaVisible, optionsForCustomInputArea);
    this.buttonsContainer = buttonsContainer;
    this.buttons = {};
    this.buttonsToLockOnRun = [];

    // add buttons to cell
    const codeIsShown = this.recreationDetails[CELL_METADATA.CODE_HIDDEN] === false;
    const tableIsShown = !this.recreationDetails[CELL_METADATA.TABLE_HIDDEN];

    this.addButton(
      'code',
      ['show', 'hide'],
      ['code-show', 'code-hide'],
      codeIsShown ? 'hide' : 'show',
    );
    this.type === 'import'
      && this.addButton(
        'table',
        ['show', 'hide'],
        ['table-show', 'table-hide'],
        tableIsShown ? 'hide' : 'show',
      );
    this.buttonsToLockOnRun.push(
      this.addButton('run', ['run'], ['code-run']),
      this.addButton('copy', ['copy'], ['code-copy']),
      this.addButton('edit', ['edit'], ['code-edit']),
    );

    // add key events to cell
    this.element[0].addEventListener('keydown', (event) => keyDownHandler(event, this));
  };


  MSTRCell.prototype.addButton = function (id, states, names, _defaultState = null) {
    const defaultState = _defaultState || states[0];
    const props = {};
    states.forEach((state, index) => {
      props[state] = {
        icon: `icons/${names[index]}.png`,
        func: this.getFunction(names[index]),
        tooltip: this.getTooltip(names[index]),
      };
    });
    this.buttons[id] = new CellButton(this.buttonsContainer, defaultState, props, id);
    return this.buttons[id];
  };


  MSTRCell.prototype.getFunction = function (funcName) {
    const out = this.buttonsFunctions[funcName];
    if (!out) throw new Error(`MSTRCell error: button function for '${funcName}' not set.`);
    return out;
  };


  MSTRCell.prototype.getTooltip = function (tooltipName) {
    const out = this.buttonsTooltips[tooltipName];
    if (!out) throw new Error(`MSTRCell error: button tooltip for '${tooltipName}' not set.`);
    return out;
  };


  MSTRCell.prototype.select = function (...args) {
    // apply default code cell behaviour first
    // returns BOOL: true => was already selected
    !Cell.prototype.select.apply(this, args) && this.focus();
  };


  MSTRCell.prototype.execute = function () {
    // [cannot use CodeCell.prototype.execute.apply(this, args) due to the structure of default implementation]
    this.isRunning = true;
    this.events.trigger('execute.MSTRCell', { cell: this });
    this.outputTable = null;

    this.clear_output(false, true);

    const oldMsgId = this.last_msg_id;
    if (oldMsgId) {
      this.kernel.kernel.clear_callbacks_for_msg(oldMsgId);
      delete CodeCell.msg_cells[oldMsgId];
      this.last_msg_id = null;
    }

    this.set_input_prompt('*');
    this.element.addClass('running');

    const callbacks = this.get_callbacks();

    // this.get_text() return content of original InputCell as string, just in case ;)
    this.engine().applyInstructions();
    this.kernel
      .setCallbacks(callbacks)
      .callChainedMethodIf(this.type && this.type !== 'import', 'shell')
      .execute()
      .then(() => {
        if (this.type === 'import') {
          this.outputTable = this.output_area.element.find('.dataframe tbody');
          this.metadata[CELL_METADATA.TABLE_HIDDEN] && this.hideTable();
        }
        flagImportExport(false);
        this.isRunning = false;
        this.events.trigger('finished_execute.MSTRCell', { cell: this });
      });

    this.kernel.getMsgId.then((id) => {
      this.last_msg_id = id;
      CodeCell.msg_cells[this.last_msg_id] = this;

      this.render();
      flagImportExport(true);
    });
  };


  MSTRCell.prototype.metadataAdd = function (object) {
    this.metadata = {
      ...this.metadata,
      ...object,
    };
  };

  MSTRCell.prototype.metadataRemove = function (key) {
    // applied this way as cell.metadata is a getter/setter so direct delete does not work
    if (this.metadata[key]) {
      const data = this.metadata;
      delete data[key];
      this.metadata = data;
    }
  };


  MSTRCell.prototype.hideTable = function () {
    this.outputTable && this.outputTable.addClass('force-hidden');
    this.metadataAdd({ [CELL_METADATA.TABLE_HIDDEN]: true });
  };

  MSTRCell.prototype.showTable = function () {
    this.outputTable && this.outputTable.removeClass('force-hidden');
    this.metadataAdd({ [CELL_METADATA.TABLE_HIDDEN]: false });
  };


  MSTRCell.prototype.focus = function () {
    this.element && !this.isRunning && this.element[0].focus();
  };
  // ===


  return MSTRCell;
});
