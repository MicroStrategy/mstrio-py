define(['./python-code'], (PythonCode) => class JupyterKernel {
  constructor(kernel, ...args) {
    if (args.length) {
      if ('url' in args[0] || 'loginMode' in args[0]) {
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

    this.kernel = kernel;
    this.getPythonCode = new PythonCode(...args);
    this.command = Promise.resolve({});
    this.msgId = null;
    this.customCallbacks = {};
    this.result = {};
    this.codeString = '';
    this.shellOnly = false;
    this.expectStreamIndex = undefined;
    this.expectJSON = true;
    this.showDebug = false;
    this.hasCell = false;
    this.doneFlag = false;
    this._id = 0;

    // workaround for Safari:
    // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions/Arrow_functions#Browser_compatibility
    this.debug = this.debug.bind(this);
    this.setIsAttachedToCell = this.setIsAttachedToCell.bind(this);
    this.formattedCallbacks = this.formattedCallbacks.bind(this);
    this.replySuccessful = this.replySuccessful.bind(this);
    this.executePythonCodeInBackground = this.executePythonCodeInBackground.bind(this);
    this.callChainedMethodIf = this.callChainedMethodIf.bind(this);
    this.code = this.code.bind(this);
    this.shell = this.shell.bind(this);
    this.stream = this.stream.bind(this);
    this.expectString = this.expectString.bind(this);
    this.setCallbacks = this.setCallbacks.bind(this);
    this.verifyCallbackType = this.verifyCallbackType.bind(this);
    this.execute = this.execute.bind(this);
    this.done = this.done.bind(this);
    this.then = this.then.bind(this);
    this.getResult = this.getResult.bind(this);
    this.parseResult = this.parseResult.bind(this);
    this.applySameOnEachElement = this.applySameOnEachElement.bind(this);
    this.setCustomEnvironmentEngine = this.setCustomEnvironmentEngine.bind(this);
    this.resetCustomEnvironment = this.resetCustomEnvironment.bind(this);
    this.updateCustomEnvironment = this.updateCustomEnvironment.bind(this);
    this.verifyCustomEnvironment = this.verifyCustomEnvironment.bind(this);


    this.replyMessageTypes = { // docs: https://jupyter-client.readthedocs.io/en/stable/messaging.html
      // expected and wanted:
      stream: 'stream',
      executeResult: 'execute_result',

      // unexpected (no mstrio code should expect it):
      displayData: 'display_data',
      updateDisplayData: 'update_display_data',
      executeInput: 'execute_input',

      // erroneous:
      error: 'error',
    };
  }


  // functions for main engine of the class
  debug() {
    this.showDebug = true;
    return this;
  }

  setIsAttachedToCell() {
    this.hasCell = true;
    return this;
  }

  get getMsgId() {
    const isNull = () => !this.msgId;
    return new Promise((resolve, reject) => {
      const returnId = (retry = 0) => {
        retry > 100 && reject(); // handler where you request msgId without fireing execute()
        if (!isNull()) {
          const out = this.msgId;
          this.msgId = null;
          resolve(out);
        } else {
          setTimeout(() => returnId(retry + 1), 50);
        }
      };
      returnId();
    });
  }

  get id() { // creates and returns unique number for kernel to recognize callbacks stack order
    window.jupyterKernelUniqueID += 1;
    this._id = window.jupyterKernelUniqueID;
    return this._id;
  }

  static awaitAll(allJupyterKernelInstances, awaitSpecificallyForDoneFlag = false) {
    if (!awaitSpecificallyForDoneFlag) {
      const allPromises = allJupyterKernelInstances.map(({ command }) => command);
      return Promise.all(allPromises);
    }
    // for the below to work, all instances need to fire "instance.done()" as the last instruction
    return new Promise((resolve, reject) => {
      let retryCount = 0;
      const interval = setInterval(
        () => { // await for all instances to have doneFlag = true;
          const ready = allJupyterKernelInstances.every((instance) => instance.doneFlag);
          if (ready) {
            clearInterval(interval);
            // reset flags for instances to be reusable
            allJupyterKernelInstances.forEach((instance) => { instance.doneFlag = false; });
            resolve(allJupyterKernelInstances);
          }
          retryCount += 1;
          if (retryCount > 400) { // 20sek
            clearInterval(interval);
            reject(new Error('JupyterKernel.awaitAll() Error: timeout'));
          }
        }, 50,
      );
    });
  }

  formattedCallbacks(callbackObject, defaultValues = null) { // NOSONAR
    /* This is object related to Jupyter Kernel
    * When used as second argument in Jupyter.notebook.kernel.execute,
    * you can control what happens with output of python code
    * {param} callbackObject: Object: object with callbacks to return which can lack some and will be "cleared"
    * {param} defaultValues: Object (opt): already cleared object with default values
    */
    const reply = callbackObject.shell && callbackObject.shell.reply
      ? callbackObject.shell.reply
      : defaultValues ? defaultValues.shell.reply : () => undefined; // NOSONAR
    const payload = callbackObject.shell && callbackObject.shell.payload
      ? callbackObject.shell.payload
      : defaultValues ? defaultValues.shell.payload : {}; // NOSONAR
    const output = callbackObject.iopub && callbackObject.iopub.output
      ? callbackObject.iopub.output
      : defaultValues ? defaultValues.iopub.output : () => undefined; // NOSONAR
    const clearOutput = callbackObject.iopub && callbackObject.iopub.clear_output
      ? callbackObject.iopub.clear_output
      : defaultValues ? defaultValues.iopub.clear_output : () => undefined; // NOSONAR
    const input = callbackObject.input
      ? callbackObject.input
      : defaultValues ? defaultValues.input : undefined; // NOSONAR
    const clearOnDone = callbackObject.clear_on_done
      ? callbackObject.clear_on_done
      : defaultValues ? defaultValues.clear_on_done : true; // NOSONAR

    return {
      shell: {
        reply, // callback function fired after shell execution status is returned
        payload, // object with callback functions fired when server require additional POST data
      },
      iopub: {
        output, // callback function fired after output for Output Cell is ready
        clear_output: clearOutput, // callback function fired after output is cleared
      },
      input, // callback function fired when some input is required
      clear_on_done: clearOnDone,
    };
  }

  get successReplies() {
    const { executeResult, stream } = this.replyMessageTypes;
    return this.expectStreamIndex ? [executeResult, stream] : [executeResult];
  }

  replySuccessful(reply, expected = this.successReplies) { return expected.includes(reply); }

  executePythonCodeInBackground() { // NOSONAR
    let responseNumber = 0;
    const expectedId = this.id; // makes sure that stack of requests refer to proper instance of this class
    const that = { ...this };

    return (
      new Promise((resolve, reject) => {
        const solution = {
          code: that.codeString,
          shell: null,
        };

        const waitForAllCallbacks = (retryNumber = 0) => {
          retryNumber > 100 && reject(new Error('executePythonCodeInBackground timed out. Please retry.'));
          Object.values(solution).every((value) => !!value) && resolve(solution);
          setTimeout(waitForAllCallbacks, 50, retryNumber + 1);
        };

        const clearedCustomCallbacks = that.formattedCallbacks(that.customCallbacks);
        const propertiesArgument = {
          shell: {
            reply: (out, ...args) => {
              if (expectedId !== that._id) return;
              clearedCustomCallbacks.shell.reply(out, ...args);
              solution.shell = out;
              this.shellOnly = false;
              if (out.msg_type === 'execute_reply' && out.content.status === 'ok') {
                console.assert(!that.showDebug, 'Successful resolution: ', solution);
                waitForAllCallbacks();
              } else { // reject overall
                reject(solution);
              }
            },
          },
        };
        if (!that.shellOnly) {
          solution.output = null;
          propertiesArgument.iopub = {
            output: (out, ...args) => {
              if (expectedId !== that._id) return;
              clearedCustomCallbacks.iopub.output(out, ...args);
              if (that.replySuccessful(out.msg_type)) {
                if (that.expectStreamIndex) {
                  responseNumber += 1;
                  console.assert(!that.showDebug, `RESPONSE #${responseNumber}:`, out);
                  if (responseNumber !== that.expectStreamIndex) return;
                  console.assert(!that.showDebug, 'EXPECTED RESPONSE INDEX, saving...');
                }
                solution.output = out;
                if (!that.hasCell && !that.expectStreamIndex) {
                  solution.output.content.data.parsed = that.parseResult(solution);
                }
              }
            },
          };
        }

        const props = that.formattedCallbacks(propertiesArgument, clearedCustomCallbacks);
        console.assert(!that.showDebug, `CODE TO EXECUTE:\n${that.codeString}`);
        console.assert(!that.showDebug, 'PROPERTIES FOR EXECUTION: ', props);
        this.msgId = that.kernel.execute(that.codeString, props, {
          silent: false,
          store_history: that.hasCell,
          stop_on_error: true,
        });
      })
    );
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

  code(input, ...args) {
    /*
     * when providing the code for execution, you can access previous execution's output
     * by providing "input" as function with one parameter instead of straight string.
     * Then, the parameter will be previous execution's output.content.data["text/plain"] parsed with JSON.parse()
     */
    this.customCallbacks = {};
    switch (typeof input) {
      case 'function':
        this.codeString = input(this.getResult());
        break;
      case 'object':
        this.codeString = this.getPythonCode[input.name](...args);
        break;
      default: this.codeString = input;
    }
    if (typeof this.codeString !== 'string') {
      throw new Error('JupyterKernel error: code to execute is not in string format (cannot execute object as string)');
    }
    console.assert(!this.showDebug, `APPLIED CODE:\n${this.codeString}`);
    return this;
  }

  shell() {
    console.assert(!this.showDebug, 'APPLY ON SHELL ONLY');
    this.shellOnly = true;
    return this;
  }

  stream(responseIndex = 1) {
    // responseIndex => which response from streamed data flow is the expected one (1 = first)
    console.assert(!this.showDebug, 'EXPECT STREAM RESPONSE, INDEX: ', responseIndex);
    this.expectStreamIndex = responseIndex;
    return this;
  }

  expectString() {
    // for when the python code do not return JSONified object, but a string (or number)
    this.expectJSON = false;
    return this;
  }

  setCallbacks(object) {
    /* Allows to provide custom callback functions into executePythonCodeInBackground
     * need to have a format of this.properties() return object
    */
    this.customCallbacks = object;
    return this;
  }

  verifyCallbackType(input) {
    if (typeof input !== 'function') {
      throw new Error('JupyterKernel syntax error: cannot fire not a function as callback');
    }
  }

  execute(_catchCallback) {
    /* _catchCallback should expect one argument
     * param @error: reference to the error outputted by executePythonCodeInBackground
     */
    const catchCallback = _catchCallback || ((error) => {
      error.code && console.error(`CODE ERRORED:\n${error.code}`);
      console.error('JupyterKernel error: executePythonCodeInBackground threw an error: ', error);
    });
    this.verifyCallbackType(catchCallback);
    console.assert(!(this.showDebug && !!_catchCallback), 'CUSTOM CATCH CALLBACK: ', catchCallback);
    this.command = this
      .executePythonCodeInBackground()
      .catch(catchCallback);
    console.assert(!this.showDebug, 'FRESH PROMISE IN EXECUTION: ', this.command);
    return this;
  }

  done() {
    return ( // returns this
      this.then((self) => {
        self.doneFlag = true;
      })
    );
  }

  then(callback) {
    /* callback should expect two arguments
     * param @self: reference to the instance of this class
     * param @output: reference to the output = meaning kernel execution object
     */
    this.verifyCallbackType(callback);
    this.command
      .then((out) => {
        this.result = out;
        callback(this, out);
      });
    return this;
  }

  getResult() {
    if (this.result.output.content.data) return this.result.output.content.data.parsed || null;
    return this.result.output.content.text.trim() || null;
  }

  parseResult(_forcedResult) { // NOSONAR
    const result = (_forcedResult || this.result).output;
    console.assert(!this.showDebug, 'RESULT TO PARSE: ', result);
    try {
      if (result.content.data) {
        let output = result.content.data['text/plain'];
        output = output.replace(/'/gi, '"');
        output = output.replace(/\\\\"/ig, '\\"');
        output = output.replace(/\\\\\//ig, '/');
        const toParse = output.charAt(0) === '"' ? output.slice(1, -1) : output;
        const toReturn = this.expectJSON
          ? JSON.parse(toParse)
          : toParse;
        console.assert(!this.showDebug, `PARSED RESULT:\n${toReturn}`);
        return toReturn;
      }
      return result.content.text.trim();
    } catch (err) {
      console.error('JSON.parse() failed with this object: ', result);
      console.error(err);
      throw new Error('JupyterKernel error: result parsing failed');
    }
  }

  applySameOnEachElement(iterableObject, callback) {
    /* callback function should expect two arguments
     * param @item: reference to specific item in iterableObject
     * param @self: reference to instance of this class
     */
    this.verifyCallbackType(callback);
    iterableObject.forEach((item) => {
      this.then((self) => {
        callback(item, self);
      });
    });
    return this;
  }
  // ---


  setCustomEnvironmentEngine() {
    this.then((self) => {
      self
        .code(PythonCode.code().forInitialEngine)
        .shell()
        .execute(() => undefined);
    });
    return this;
  }

  resetCustomEnvironment() {
    const { customEnvironment } = this.otherDetails;
    this.then((self) => {
      self
        .code(`${customEnvironment} = create_custom_env()`)
        .shell()
        .execute(() => undefined);
    });
    return this;
  }

  updateCustomEnvironment() {
    const { customEnvironment } = this.otherDetails;
    this.then((self) => {
      self
        .code(`${customEnvironment} = update_custom_env()`)
        .shell()
        .execute(() => undefined);
    });
    return this;
  }

  verifyCustomEnvironment() {
    const { customEnvironment } = this.otherDetails;
    this
      .then((self) => {
        self
          .code((`
if '${customEnvironment}' in locals():
    ${customEnvironment} = update_custom_env()
else:
    ${customEnvironment} = create_custom_env()
          `).trim())
          .shell()
          .execute(() => undefined);
      });
    return this;
  }
});
