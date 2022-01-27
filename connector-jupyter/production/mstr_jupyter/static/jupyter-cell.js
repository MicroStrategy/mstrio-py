define([
  './python-code', './jupyter-kernel', './cell-button', './mstr-cell', './utilities', './globals',
], (
  PythonCode, JupyterKernel, CellButton, MSTRCell, Utilities, { CELL_METADATA, GLOBAL_CONSTANTS },
) => class JupyterCell {
  constructor(notebook, ...args) {
    this.notebook = notebook;

    if (args.length === 1) { // reapplying on existing cell
      [this.recreationDetails] = args;
      const data = this.recreationDetails[CELL_METADATA.DATA];
      const argsForNewJupyterKernel = [
        data.authenticationDetails,
        data.dataframeDetails,
        data.otherDetails,
      ];
      this.kernel = new JupyterKernel(this.notebook.kernel, ...argsForNewJupyterKernel).setIsAttachedToCell();
      this.type = this.recreationDetails[CELL_METADATA.TYPE];
    } else { // creating new cell
      this.recreationDetails = args[3] || {};
      this.kernel = new JupyterKernel(this.notebook.kernel, ...args).setIsAttachedToCell();
      this.type = null;
    }

    this.codeInstructions = {};
    this.cell = null;

    // workaround for Safari:
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions#Browser_compatibility
    this.notebookChangedFlag = this.notebookChangedFlag.bind(this);
    this.callChainedMethodIf = this.callChainedMethodIf.bind(this);
    this.insertAt = this.insertAt.bind(this);
    this.setCodeFunctional = this.setCodeFunctional.bind(this);
    this.setCodeVisible = this.setCodeVisible.bind(this);
    this.setCode = this.setCode.bind(this);
    this.newCell = this.newCell.bind(this);
    this.setInstructions = this.setInstructions.bind(this);
    this.applyInstructions = this.applyInstructions.bind(this);
    this.showCodeIfViable = this.showCodeIfViable.bind(this);
    this.execute = this.execute.bind(this);
    this.select = this.select.bind(this);
    this.removePrevious = this.removePrevious.bind(this);
    this.createCell = this.createCell.bind(this);
    this.recreateCell = this.recreateCell.bind(this);
    this.forType = this.forType.bind(this);
    this.forImport = this.forImport.bind(this);
    this.forExport = this.forExport.bind(this);
    this.forUpdate = this.forUpdate.bind(this);
  }

  notebookChangedFlag() {
    this.notebook.set_dirty(true);
    return this;
  }

  callChainedMethodIf(logicalTest, methodName, ...args) {
    /**
     * method allowing chaining with "if-ed" methods inside chain:
     * EG. when you want to do something like:
     *
     * if (a === b) this.code().shell('test').execute()
     * else this.code().execute()
     *
     * you can use shortcut through "callChainedMethodIf" like this:
     * (method ".shell('test')" will be fired inside chain only when a === b)
     *
     * this.code().callChainedMethodIf(a === b, 'shell', 'test').execute()
     */
    if (logicalTest) {
      this[methodName](...args);
    }
    return this;
  }

  insertAt(_index = null) {
    const cellsCount = this.notebook.ncells();
    let index = _index === null
      ? cellsCount
      : cellsCount === 0 // NOSONAR
        ? 0
        : _index < 0 // NOSONAR
          ? cellsCount + _index + 1
          : _index;
    index > cellsCount && (index = cellsCount);
    index < 0 && (index = 0);
    // eslint-disable-next-line camelcase
    const { events, config, keyboard_manager, tooltip } = this.notebook;

    this.cell = new MSTRCell(this.kernel, {
      index,
      events,
      config,
      keyboard_manager,
      tooltip,
      notebook: this.notebook,
      type: this.type,
      engine: () => this,
    }, this.recreationDetails);

    // set proper code values
    this.setCodeFunctional('', `${JupyterCell.noExtensionComment()}\n\n${this.cell.codePrefix}`);
    this.setCodeVisible('', this.cell.codePrefix);

    return this // returns "this"
      .notebookChangedFlag();
  }

  setCodeFunctional(code = '', prefix = '') {
    this.cell.set_text(`${prefix}${prefix && code ? '\n\n' : ''}${code}`);
    return this;
  }

  setCodeVisible(code = '', prefix = '') {
    this.cell.customInputArea.setValue(`${prefix}${prefix && code ? '\n\n' : ''}${code}`);
    return this;
  }

  setCode(code = '', prefix = '') {
    return ( // returns "this"
      this
        .setCodeFunctional(code, prefix)
        .setCodeVisible(code, prefix)
    );
  }

  newCell(type) {
    this.type = type;
    if (!JupyterCell.isValidType(this.type)) throw new Error('JupyterCell error: undefined cell type set');
    return this;
  }

  setInstructions(input, ...args) {
    this.codeInstructions = {
      input,
      args,
    };
    this.kernel.code(input, ...args);
    return this;
  }

  applyInstructions() {
    const { input, args } = this.codeInstructions;
    if (!input) {
      throw new Error(
        'JupyterCell error: cannot apply instructions when they are not set.'
        + 'Use this.setInstructions(input, ...args) instead.',
      );
    }
    this.kernel.code(input, ...args);
    return this;
  }

  showCodeIfViable() {
    if (!this.cell.metadata[CELL_METADATA.CODE_HIDDEN]) { // cannot be "undefined" at this point
      CellButton.functions(this.cell)['code-show']();
    }
    return this;
  }

  execute() {
    new JupyterKernel(
      this.kernel,
      { customEnvironment: GLOBAL_CONSTANTS.MSTR_ENV_VARIABLE_NAME },
    ).setCustomEnvironmentEngine();

    this.cell.execute();
    return this;
  }

  select() {
    this.cell.select();
    return this;
  }

  removePrevious(index) {
    this.notebook.delete_cell(index);
    return this;
  }

  createCell(type, forcedIndex = null) {
    return (this.newCell(type) // function creating cell from scratch
      .insertAt(
        forcedIndex !== null
          ? forcedIndex
          : (this.type === 'import' ? 0 : null), // NOSONAR
      )
      .setInstructions(PythonCode.code()[`for${Utilities.properCase(this.type)}`])
      .execute()
      .setInstructions(PythonCode.code()[`for${Utilities.properCase(this.type)}`], true)
      .showCodeIfViable());
  }

  recreateCell(index) {
    return (this.removePrevious(index) // function reapplying new cell engine to existing cell
      .insertAt(index)
      .setInstructions(PythonCode.code()[`for${Utilities.properCase(this.type)}`], true)
      .showCodeIfViable());
  }

  forType(type, index = null) {
    return this.createCell(type, index);
  }

  // functionalities to fire in main.js
  forImport(forcedIndex = null) { return this.forType(JupyterCell.cellTypes().import, forcedIndex); }
  forExport(forcedIndex = null) { return this.forType(JupyterCell.cellTypes().export, forcedIndex); }
  forUpdate(forcedIndex = null) { return this.forType(JupyterCell.cellTypes().update, forcedIndex); }

  // static values
  static cellTypes() {
    return {
      import: 'import',
      export: 'export',
      update: 'update',
    };
  }

  static isValidType(type) { return Object.values(JupyterCell.cellTypes()).includes(type); }

  static noExtensionComment() {
    return (`
# IMPORTANT: This cell was generated by MicroStrategy for Jupyter.
# To ensure full functionality, please install the latest add-in version.
# (https://community.microstrategy.com/s/products)
  `.trim());
  }
});
