define(['./python-code', './jupyter-kernel'], (PythonCode, JupyterKernel) => class JupyterCell {
  constructor(notebook, ...args) {
    if (args.length) {
      if ('username' in args[0]) {
        [
          this.authenticationDetails,
          this.dataframeDetails,
          this.otherDetails,
        ] = args;
      } else if ('customEnvironment' in args[0]) {
        [this.otherDetails] = args;
      } else {
        [
          this.dataframeDetails,
          this.otherDetails,
        ] = args;
      }
    }

    this.getPythonCode = new PythonCode(...args);
    this.notebook = notebook;
    this.kernel = new JupyterKernel(this.notebook.kernel, ...args);
    this.steps = [];
  }

  // Jupyter Notebook Control functions
  get cell() { // for readability inside this class only
    return this;
  }

  newStep = (type, value = true) => {
    this.steps.push({ type, value });
  };

  get lastStep() { // get last applied step
    return this.steps[this.steps.length - 1];
  }

  lastStepOfType = (typeToFind) => (
    [...this.steps] // dummy array because .reverse() updates in-place
      .reverse()
      .find(({ type }) => type === typeToFind)
  );

  get new() { // define if provided cell is new or existing
    if (this.lastStepOfType('cell')) {
      throw new Error('JupyterCell syntax error: "new" property can only be applied before cell index (cannot apply new to already created cell)');
    }
    this.newStep('new');
    return this;
  }

  cellSelectionPreconditions = (index = null) => {
    if (this.lastStepOfType('new') && this.steps.length === 1) {
      index === null && this.notebook.insert_cell_at_bottom('code');
      index !== null && this.notebook.insert_cell_above('code', index);
    } else if (this.lastStep) {
      throw new Error('JupyterCell syntax error: incorrect initial steps reference (unrecognized step found)');
    }
  }

  get atFirst() { // first cell
    this.cellSelectionPreconditions(-1);
    this.newStep('cell', this.notebook.get_cell(0));
    return this;
  }

  get atLast() { // last cell
    this.cellSelectionPreconditions();
    this.newStep('cell', this.notebook.get_cell(-1));
    return this;
  }

  at = (index) => { // cell at specific index
    this.cellSelectionPreconditions(index);
    this.newStep('cell', this.notebook.get_cell(index));
    return this;
  }

  insertCode = (input, ...args) => { // insert code into cell
    if (!this.lastStepOfType('cell')) {
      throw new Error('JupyterCell syntax error: no reference cell provided (cannot insert code into undefined)');
    }

    let code;
    if (typeof input === 'object') {
      code = this.getPythonCode[input.name](...args);
    } else {
      code = input;
    }

    try {
      this.newStep('code-insert', code);
    } catch (err) {
      throw new Error('JupyterCell syntax error: incorrect code value (cannot insert undefined into cell)');
    }

    return this;
  }

  execute = () => { // execute Jupyter cell
    if (!this.lastStepOfType('cell')) {
      throw new Error('JupyterCell syntax error: no reference cell provided (cannot execute undefined)');
    }
    this.newStep('execution');
    return this;
  }

  applySteps = () => { // apply all steps
    // error handling
    if (this.steps.filter(({ type }) => type === 'cell').length !== 1) {
      throw new Error('JupyterCell syntax error: incorrect number of cell references in step chain (expect one cell reference)');
    } else if (!this.lastStepOfType('cell').value) {
      throw new Error('Jupyter.notebook error inside JupyterCell: "Jupyter.get_cell()" returned undefined (check kernel connection)');
    }

    const cell = this.lastStepOfType('cell').value;
    this.steps.forEach(({ type, value }) => {
      switch (type) {
        case 'code-insert':
          cell.set_text(value); break;
        case 'execution':
          cell.execute(); break;
        default: break;
      }
    });
    cell.metadata.mstr_cell = true;
    this.steps = [];
  }
  // ---

  /* TO CONSIDER
   * if those three functions end up looking similar after further development
   * please refer to the following comment
   * https://github.microstrategy.com/Kiai/mstrio-py/pull/278#discussion_r124768
  */
  forImport = () => { // create cell for Importing specific Cube / Report
    this.cell
      .new.atFirst
      .insertCode(this.getPythonCode.forImport())
      .execute()
      .insertCode(this.getPythonCode.forImport(true))
      .applySteps();
  }


  forExport = () => { // create cell for Exporting specific Cube / Report
    this.cell
      .new.atLast
      .insertCode(this.getPythonCode.forExport())
      .execute()
      .insertCode(this.getPythonCode.forExport(true))
      .applySteps();
  }


  forUpdate = () => { // create cell for Updating specific Cube / Report
    this.cell
      .new.atLast
      .insertCode(this.getPythonCode.forUpdate())
      .execute()
      .insertCode(this.getPythonCode.forUpdate(true))
      .applySteps();
  }
});
