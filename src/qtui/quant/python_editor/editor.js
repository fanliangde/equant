//////////////////////////////////////////////////////////////////////////////
// 文件名：editor.js
// 作者：  刘明祥
// 功能：  实现VScode中的代码编辑器调用, 在网页中嵌入monaco.editor，并在本地进程中嵌入一个浏览器打开该网页
//        在网页中创建websocket客户端和同一本地进程里的websocket服务端通信来完成代码文件的加载与保存
//
// JSON格式的协议：
// 设置主题
// {"cmd":"settheme", theme":"", "fontsize":12}
// 打开文件
// {"cmd":"openfile", "file":"", "txt":""}
// 保存文件
// {"cmd":"savefile_req", "file":""}
// {"cmd":"savefile_rsp", "file":"", "txt":""}
// 文件修改通知
// {"cmd":"modifyfile_nty", "file":"", "modified":true}
// 标签切换
// {"cmd":"switchfile_nty", "file":""}
// 键盘事件
// {"cmd":"do_key_event", "keys":[17, 86]}
//////////////////////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////////////////////
///代码编辑器 monaco.editor
//////////////////////////////////////////////////////////////////////////////
///
//当前代码编辑器所打开的文件，为空则为新建文件
var g_model = null;
var g_filename = "";
var g_loading = false;
var g_ready = false;
//编辑器实例
var g_editor = null;


//初始化编辑器
function init_editor(layoutid, code_str, theme) {
    if (g_editor)
        return;	    
    
    //初始化编辑器
    require.config(
        {
            paths: {'vs': 'monaco-editor/package/min/vs'},
            'vs/nls': {availableLanguages: {'*': 'zh-cn'}}
        }
    );
    require(['vs/editor/editor.main'], function () {
        g_editor = monaco.editor.create(
            document.getElementById(layoutid),
            {
                language: 'python',             //程序语言
                theme: theme,                   //界面主题
                value: code_str,                //初始文本内容
                automaticLayout: true,          //随布局Element自动调整大小                        
                minimap: {enabled: true},       //代码略缩图
                fontSize: 14,                   //字体大小
                //wordWrap: "on",               //自动换行，注意大小写
                wrappingIndent: "indent",       //自动缩进
                //glyphMargin: true,            //字形边缘
                //useTabStops: false,           //tab键停留
                //selectOnLineNumbers: true,    //单击行号选中该行
                //roundedSelection: false,      //
                //readOnly: false,              //只读
                //cursorStyle: 'line',          //光标样式
                //autoIndent:true,              //自动布局
                //quickSuggestions: false,
                //quickSuggestionsDelay: 500,   //代码提示延时
                contextmenu: true,
                //fontFamily:'Consolas',
                lineNumbersMinChars: 5,
                scrollBeyondLastLine: true,
                lineHeight: 24,
                mouseWheelZoom: true,
                scrollbar: {
                    vertical: 1,
                    horizontal: 1,
                    useShadows: true,
                    horizontalSliderSize: 7,
                    verticalSliderSize: 7,
                    horizontalScrollbarSize: 7,
                    verticalScrollbarSize: 7,
                },
            }
        );

        g_editor.onDidChangeModelContent(function(v) {
            if (!g_loading && g_filename)
                modify_nty(g_filename, org_datas[g_filename] != g_editor.getValue());
        });

        disable_drag();
        add_completions();
        add_contextmenu();
        init_function_info();
    });

    //自适应大小，可以不要
    window.onresize = do_size;
    //编辑器加载成功后创建websocket连接
    window.onload = do_load;
}

//自适应窗口大小
function do_size() {
    if (g_editor)
        g_editor.layout()
}

function do_load() { 
    //init_webskt();
    g_ready = true;
}

//设置主题风格 theme:vs-dark vs hc-black, fontsize:S M L XL XXL
function set_theme(theme, fontsize) {
    monaco.editor.setTheme(theme);

    const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
    ind = sizes.indexOf(fontsize);
    if (ind < 0)
        return;
    fsize = 14 + 2 * ind;
    lsize = Math.ceil(fsize * 1.7);
    if (lsize % 2 == 1)
        lsize -= 1;
    g_editor.updateOptions({ fontSize: fsize, lineHeight: lsize, });
}

//设置代码文件
function load_file(file, txt) {
    g_loading = true;
    g_filename = file;
    g_editor.setValue(txt);
    g_loading = false;
}

//重命名
function rename_file(file, newfile) {
    rename_tab(file, newfile);
    if (file == g_filename)
        g_filename = newfile;
}

//关闭标签
function close_file(file){
    close_tab(file)
}

//保存代码到本地文件, need_confirm为true时需要用户确认是否保存，否则不需要用户确认直接保存
function save_file(file, need_confirm) {
    if (file == g_filename)
        datas[file] = g_editor.getValue()
	
    org_datas[file] = datas[file];
    on_modify(file, false);
    
    // data = {
    //     'cmd':'savefile_rsp',
    //     'file':file,
    //     'txt':datas[file]
    // };
    // senddata(data);

    Bridge.do_save_file(file, datas[file], need_confirm);
}
//切换文件
function switch_file(file){
    // data = {
    //     'cmd':'switch_file',
    //     'file':file
    // };
    // senddata(data);

    Bridge.on_switch_file(currtab);
}
//文件被修改
function modify_nty(file, modified) {
    on_modify(file, modified);
    
    // data = {
    //     'cmd':'modify_nty',
    //     'file':file,
    //     'modified': modified
    // };
    // senddata(data);
    
    Bridge.on_modify_file(file, modified);
}
//粘贴
function do_key_event(){
    // data = {
    //     'cmd':'do_key_event',
    //     'keys':[17, 86], // Ctrl+V
    //     'is_group':true
    // };
    // senddata(data);
    
    Bridge.do_key_event([17, 86], true);
}
//文件修改通知
function on_modify(file, modified) {
    var tab = $(file);
    if (!tab)
        return;
    var btn = tab.children[0];
    if (!btn)
        return;

    if (modified)
        btn.className = 'modify_btn';
    else if (tab.id == currtab)
        btn.className = 'curr_btn';
    else if (tab.id == overtab)
        btn.className = 'over_btn';
    else
        btn.className = '';
}



//////////////////////////////////////////////////////////////////////////////
/// 标签栏管理
//////////////////////////////////////////////////////////////////////////////
///
// == 值比较  === 类型比较 $(id) ---->document.getElementById(id)
function $(id){
    return typeof id === 'string' ? document.getElementById(id):id;
}
 
//全局字典 file->content
var datas = new Array();
var org_datas = new Array();

// 当前标签
var currtab = "";
var overtab = "";

function close_tab(id){
    var tab = $(id.toString())
    if (!tab)
        return;

    if (tab.className == 'current')
    {
        var _tab = tab.nextElementSibling;
        if (!_tab)
            _tab = tab.previousElementSibling;
        switch_tab(_tab ? _tab.id : '');
    }

    delete datas[id];
    delete org_datas[id];
    tab.remove();
}

function rename_tab(id, newid){
    var tab = $(id.toString())
    if (!tab)
        return;
    var btn = tab.children[0];
    tab.id = newid;
    tab.innerHTML = newid.substr(newid.lastIndexOf('/')+1);
    tab.appendChild(btn);

    datas[newid] = datas[id];
    org_datas[newid] = org_datas[id];
    delete datas[id];
    delete org_datas[id];
}

// 切换标签
function switch_tab(newtab) {
    if (newtab == currtab)
        return;

    var tab_new = $(newtab.toString());
    if (!tab_new && newtab != "")
        return;

    var tab_old = $(currtab.toString())
    if (tab_old){
        tab_old.className = '';
        var btn = tab_old.children[0];
        if (btn && btn.className != 'modify_btn')
            btn.className = '';

       datas[currtab] = g_editor.getValue();
    }
    
    currtab = newtab;
    if (tab_new){
        tab_new.className = 'current';
        var btn = tab_new.children[0];
        if (btn && btn.className != 'modify_btn')
            btn.className = 'curr_btn';
    }
    load_file(currtab, tab_new ? datas[currtab] : '');
    switch_file(currtab);
}

// 添加标签
function add_tab(name, value){
    if (name == "")
        return;
    if (datas.hasOwnProperty(name)){
        switch_tab(name);
        return;
    }

    //新建标签
    var tab = document.createElement("li");
    tab.id = name;
    tab.innerHTML = name.substr(name.lastIndexOf('/')+1);

    //新建关闭按钮
    var btn = document.createElement("a");
    btn.href = "#";
    btn.innerHTML = "x";

    //添加按钮到标签上
    tab.appendChild(btn);
    //添加按钮到标签栏上
    $('tabs').appendChild(tab);

    //设置标签和按钮的单击事件
    tab.onclick = function(){
        switch_tab(this.id);
    }
    btn.onclick = function(){
        var tab = this.parentNode;
        if (tab.className == 'current')
        {
            var _tab = tab.nextElementSibling;
            if (!_tab)
                _tab = tab.previousElementSibling;
            switch_tab(_tab ? _tab.id : '');
        }
        if (org_datas[tab.id] != datas[tab.id])
            save_file(tab.id, true);

        delete datas[tab.id];
        delete org_datas[tab.id];
        tab.remove();
    }
    tab.onmouseover = function(){
        overtab = this.id;
        var btn = this.children[0];
        if (btn && btn.className != 'curr_btn' && btn.className != 'modify_btn')
            btn.className = 'over_btn';
    }
    tab.onmouseout = function(){ 
        overtab = "";
        var btn = this.children[0];
        if (btn && btn.className != 'curr_btn' && btn.className != 'modify_btn')
            btn.className = '';
    }


    //添加标签关联的数据
    datas[name] = value;
    org_datas[name] = value;
    //切换到新标签
    switch_tab(name);
}



//////////////////////////////////////////////////////////////////////////////
///Qt web客户端通道
//////////////////////////////////////////////////////////////////////////////
try{
    new QWebChannel(qt.webChannelTransport,
        function (channel) {
            window.Bridge = channel.objects.Bridge;

            // 绑定自定义的信号customSignal
            Bridge.openSignal.connect(function (file, text) {
                if (g_ready)
                    add_tab(file, text);
            });
            
            Bridge.saveSignal.connect(function (file){
                save_file(file, false)
            });
            
            Bridge.renameSignal.connect(function (file, newfile){
                rename_file(file, newfile)
            });
            
            Bridge.deleteSignal.connect(function (file){
                close_file(file)
            });

            Bridge.setThemeSignal.connect(function (text) {
                set_theme(text, '');
                if (text == 'vs-dark'){
                    document.getElementById('main_link').href = 'editor.css'
                }else {
                    document.getElementById('main_link').href = 'editor_vs.css'
                }
            });
        }
    );
}catch(e){
    
}



//////////////////////////////////////////////////////////////////////////////
///websocket客户端
//////////////////////////////////////////////////////////////////////////////
///
// var ws = null;
// //判断浏览器是否内置了websocket
// function init_webskt() {
//     if (ws != null)
//         return;
//     if ('WebSocket' in window)
//         ws = new WebSocket("ws://localhost:8765");
//     else{
//         return;
//     }
    
//     //连接web socket成功触发
//     ws.onopen = function (evt){
//     }
//     //断开web socket成功触发
//     ws.onclose = function (evt){
//         ws = null;
//         setTimeout(1000);
//         init_webskt();
//     }
//     //web socket连接失败时触发
//     ws.onerror = function (evt){
//     }

//     //当窗口关闭时，关闭websocket。防止server端异常
//     ws.onbeforeunload = function (evt){
//         ws.close();
//     }

//     //接收web socket服务端数据时触发
//     ws.onmessage = function (evt) {
//         //alert(evt.data)
//         data = JSON.parse(evt.data);
//         if (data.cmd == 'openfile')
//             add_tab(data.file, data.txt);
//         else if (data.cmd == 'settheme')
//             set_theme(data.theme, data.fontsize);
//         else if (data.cmd == 'savefile_req')
//             save_file(data.file, false);
//         // else if (data.cmd == 'clipboard_rsp')
//         //     do_paste(data.txt);
//     };
// }

// //发送文本到websocket服务端
// function senddata(data) {
//     if (ws == null)
//         return;
//     json_str = JSON.stringify(data);
//     ws.send(json_str);
//     // alert(json_str)
// }




////////////////////////////////////////////////////////////////////////////////////////////
/// 屏蔽浏览器打开拖拽来的文件
////////////////////////////////////////////////////////////////////////////////////////////
function disable_drag(){
    //当拖曳元素进入目标元素的时候触发的事件，此事件作用在目标元素上
    document.addEventListener("dragenter", function( event ) {
        event.preventDefault();
        event.returnValue = false;
    }, false);
    //拖拽元素在目标元素上移动的时候触发的事件，此事件作用在目标元素上
    document.addEventListener("dragover", function( event ) {
        event.preventDefault();
        event.returnValue = false;
    }, false);
    //被拖拽的元素在目标元素上同时鼠标放开触发的事件，此事件作用在目标元素上
    document.addEventListener("drop", function( event ) {
        event.preventDefault();
        event.returnValue = false;
    }, false);
    //当拖拽完成后触发的事件，此事件作用在被拖曳元素上
    document.addEventListener("dragend", function( event ) {
        event.preventDefault();
        event.returnValue = false;
    }, false);
}


////////////////////////////////////////////////////////////////////////////////////////////
/// 添加右键菜单
////////////////////////////////////////////////////////////////////////////////////////////
function add_contextmenu() {
    var undo = g_editor.createContextKey('undo', false);
    g_editor.addAction({            
        id: 'undo_model',  label: '撤销',  contextMenuGroupId: '9_cutcopypaste',
        keybindings: [ monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_Z ],
        keybindingContext: null,  contextMenuOrder: 0,  precondition: undo.set(true),
        run: function(ed){ g_editor.trigger('', 'undo'); }
    });

    var redo = g_editor.createContextKey('redo', false);
    g_editor.addAction({            
        id: 'redo_model',  label: '重做',  contextMenuGroupId: '9_cutcopypaste',
        keybindings: [ monaco.KeyMod.Shift | monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_Z ],
        keybindingContext: null,  contextMenuOrder: 0.1,  precondition: redo.set(true),
        run: function(ed){ g_editor.trigger('', 'redo'); }
    });

    var paste = g_editor.createContextKey('paste', false);
    g_editor.addAction({            
        id: 'paste_model',  label: '粘贴　　　　　 　　　Ctrl+V',  contextMenuGroupId: '9_cutcopypaste',
        keybindings: [  ],
        keybindingContext: null,  contextMenuOrder: 8,  precondition: paste.set(true),
        run: function(ed){ do_key_event(); }
    });
    
    var selectAll = g_editor.createContextKey('selectAll', false);
    g_editor.addAction({            
        id: 'selectAll_model',  label: '全选',  contextMenuGroupId: '9_cutcopypaste',
        keybindings: [ monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_A ],
        keybindingContext: null,  contextMenuOrder: 9,  precondition: selectAll.set(true),
        run: function(ed){ g_editor.trigger('', 'selectAll'); }
    });
}


////////////////////////////////////////////////////////////////////////////////////////////
/// 代码自动完成
//////////////////////////////////////////////////////////////////////////////////////////// 
function add_completions() {
    // 代码自动完成
    monaco.languages.registerCompletionItemProvider('*', {
        provideCompletionItems: function(model, position) {
            var curr_line = model.getValueInRange({
                startLineNumber: position.lineNumber,
                startColumn    : 1,
                endLineNumber  : position.lineNumber,
                endColumn      : position.column
            }); 
            if (!curr_line)
                curr_line = '';

            return { suggestions: get_uggestions(curr_line.trim()) };
        },
        // 写触发提示的字符
        triggerCharacters: ['.'] 
    });

    // 鼠标悬停提示
    monaco.languages.registerHoverProvider('*', {
        provideHover: function(model, position) {
            var iword = model.getWordAtPosition(position);
            var curr_word = iword ? iword.word : '';
            return { contents: get_contents(curr_word) };
        }
    });

    // 函数提示(快捷键提示)
    g_editor.addCommand(monaco.KeyMod.Shift | monaco.KeyMod.CtrlCmd | monaco.KeyCode.Space, function(){
        g_editor.trigger('', 'editor.action.triggerSuggest');
        //g_editor.getContribution('editor.contrib.suggestController').triggerSuggest();
        //g_editor.trigger('', 'editor.action.showHover', {});
    });
}


function get_uggestions(curr_line) {
    var ret = [];
    if (!curr_line)
        return ret;  

    var items = curr_line.match(/(\w*)\.([a-z_A-Z]*\w*)$/);
    if (!items)
        items = curr_line.match(/([@a-z_A-Z]*\w*)$/);
    if (!items)
        return ret;

    // 有'.'
    if (items.length == 3){
        var word = items[1].toLowerCase();
        if (word == 'ta')
            word = 'talib';
        
        ret = function_info[word];
        if (!ret)
            ret = function_info['sub'];
    }else
        ret = function_info['root'];

    return ret ? ret : [];
}

function get_contents(curr_word) {
    if (!curr_word)
        return [];
    var ret = provide_hover[curr_word];
    if (!ret)
        return [];

    //支持markdown語法
    ret = ret.replace('# ', '');
    ret = ret.replace(/\n\n/g, '\n');
    ret = ret.replace(/\n/g, '\n\r');
    ret = ret.replace(/    /g, '> ');
    return [{value: ret}];    
}

////////////////////////////////////////////////////////////////////////////////////////////
/// 代码自动完成
/// 支持python关键字和操作符
/// 支持程序化的所有关键字、函数及其参数
/// 支持talib函数及其参数
//////////////////////////////////////////////////////////////////////////////////////////// 
///
// 函数信息
var function_info = {};
// provideHover
var provide_hover = {};

function init_function_info() {    
    if (function_info.length >0)
        return;

    function_info = {
        'root':[
        ////////////////////////////////////////////////////////////////////////////////////////
        // python常用值
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : 'False',
                insertText      : 'False',
                kind            : monaco.languages.CompletionItemKind.Value
            },{
                label           : 'None',
                insertText      : 'None',
                kind            : monaco.languages.CompletionItemKind.Value
            },{
                label           : 'True',
                insertText      : 'True',
                kind            : monaco.languages.CompletionItemKind.Value
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // python语法块
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : 'class',
                insertText      : 'class ${1}():',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'def',
                insertText      : 'def ${1}():',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'if',
                insertText      : 'if ${1}:',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'elif',
                insertText      : 'elif ${1}:',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'else',
                insertText      : 'else:',
                kind            : monaco.languages.CompletionItemKind.Snippet
            },{
                label           : 'for',
                insertText      : 'for ${1}:',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'while',
                insertText      : 'while ${1}:',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'continue',
                insertText      : 'continue',
                kind            : monaco.languages.CompletionItemKind.Snippet
            },{
                label           : 'return',
                insertText      : 'return',
                kind            : monaco.languages.CompletionItemKind.Snippet
            },{
                label           : 'break',
                insertText      : 'break',
                kind            : monaco.languages.CompletionItemKind.Snippet
            },{
                label           : 'try',
                insertText      : 'try:\n    ${1}',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'try:...finally:...',
                insertText      : 'try:\n    ${1}\nfinally:\n    ',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'try:...except:...',
                insertText      : 'try:\n    ${1}\nexcept:\n    ',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'finally',
                insertText      : 'finally:\n    ${1}',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'except',
                insertText      : 'except:\n    ${1}',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'raise',
                insertText      : 'raise',
                kind            : monaco.languages.CompletionItemKind.Snippet
            },{
                label           : 'with',
                insertText      : 'with ${1}:',
                kind            : monaco.languages.CompletionItemKind.Snippet,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '@classmethod',
                insertText      : '@classmethod',
                kind            : monaco.languages.CompletionItemKind.Snippet
            },{
                label           : '@staticmethod',
                insertText      : '@staticmethod',
                kind            : monaco.languages.CompletionItemKind.Snippet
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // python关键字
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : 'and',
                insertText      : 'and ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'in',
                insertText      : 'in ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'is',
                insertText      : 'is ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'not',
                insertText      : 'not ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'or',
                insertText      : 'or ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'as',
                insertText      : 'as ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'assert',
                insertText      : 'assert ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'del',
                insertText      : 'del ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'from',
                insertText      : 'from ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'global',
                insertText      : 'global ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'import',
                insertText      : 'import ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'nonlocal',
                insertText      : 'nonlocal ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'pass',
                insertText      : 'pass',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'yield',
                insertText      : 'yield',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'self',
                insertText      : 'self',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'async',
                insertText      : 'async ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'await',
                insertText      : 'await ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },{ 
                label           : 'lambda',
                insertText      : 'lambda ',
                kind            : monaco.languages.CompletionItemKind.Kyeword
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // 策略常用模块
        //////////////////////////////////////////////////////////////////////////////////////// 
            { 
                label           : 'talib',
                insertText      : 'talib ',
                kind            : monaco.languages.CompletionItemKind.Module
            },
            { 
                label           : 'numpy',
                insertText      : 'numpy ',
                kind            : monaco.languages.CompletionItemKind.Module
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // 策略常用变量
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : 'g_params',
                insertText      : 'g_params[${1}]',
                detail          : '# 策略的自定义参数字典，可在配置界面修改，形如g_params[\'qty\'] = 10',
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : 'context',
                insertText      : 'context',
                detail          : '# 策略接口函数的参数，带入策略上下文信息',
                kind            : monaco.languages.CompletionItemKind.Variable
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // 策略接口函数
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : 'initialize',
                insertText      : 'initialize(context)',
                detail          : '# 策略初始化函数，策略每次运行前调用一次\n' +
                                  '    def initialize(context)',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'handle_data',
                insertText      : 'handle_data(context)',
                detail          : '# 策略执行函数，策略每次触发都会调用一次\n' +
                                  '    def handle_data(context)',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'hisover_callback',
                insertText      : 'hisover_callback(context)',
                detail          : '# 策略历史阶段执行完毕时的通知函数，策略历史数据执行完毕时调用一次\n' +
                                  '    def hisover_callback(context)',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'exit_callback',
                insertText      : 'exit_callback(context)',
                detail          : '# 策略退出时的通知函数，策略正常结束前调用一次\n' +
                                  '    def exit_callback(context)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // python常用函数
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : 'super',
                insertText      : 'super(${1})',
                detail          : '# 父类对象',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'apply',
                insertText      : 'apply(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'buffer',
                insertText      : 'buffer(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'cmp',
                insertText      : 'cmp(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'coerce',
                insertText      : 'coerce(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'execfile',
                insertText      : 'execfile(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'file',
                insertText      : 'file(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'long',
                insertText      : 'long(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'raw_input',
                insertText      : 'raw_input(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'reduce',
                insertText      : 'reduce(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'reload',
                insertText      : 'reload(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'reverse',
                insertText      : 'reverse(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'unichr',
                insertText      : 'unichr(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'xrange',
                insertText      : 'xrange(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'abs',
                insertText      : 'abs(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'all',
                insertText      : 'all(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'any',
                insertText      : 'any(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ascii',
                insertText      : 'ascii(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'bin',
                insertText      : 'bin(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'bool',
                insertText      : 'bool(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'basestring',
                insertText      : 'basestring(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'bytearray',
                insertText      : 'bytearray(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'bytes',
                insertText      : 'bytes(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'callable',
                insertText      : 'callable(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'chr',
                insertText      : 'chr(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'compile',
                insertText      : 'compile(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'complex',
                insertText      : 'complex(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'delattr',
                insertText      : 'delattr(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'dict',
                insertText      : 'dict(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'dir',
                insertText      : 'dir(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'divmod',
                insertText      : 'divmod(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'enumerate',
                insertText      : 'enumerate(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'eval',
                insertText      : 'eval(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'exec',
                insertText      : 'exec(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'filter',
                insertText      : 'filter(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'float',
                insertText      : 'float(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'format',
                insertText      : 'format(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'frozenset',
                insertText      : 'frozenset(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'getattr',
                insertText      : 'getattr(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'globals',
                insertText      : 'globals(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'hasattr',
                insertText      : 'hasattr(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'hash',
                insertText      : 'hash(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'help',
                insertText      : 'help(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'hex',
                insertText      : 'hex(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'id',
                insertText      : 'id(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'input',
                insertText      : 'input(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'int',
                insertText      : 'int(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'isinstance',
                insertText      : 'isinstance(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'issubclass',
                insertText      : 'issubclass(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'iter',
                insertText      : 'iter(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'len',
                insertText      : 'len(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'list',
                insertText      : 'list(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'locals',
                insertText      : 'locals(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'map',
                insertText      : 'map(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'max',
                insertText      : 'max(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'memoryview',
                insertText      : 'memoryview(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'min',
                insertText      : 'min(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'next',
                insertText      : 'next(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'object',
                insertText      : 'object(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'oct',
                insertText      : 'oct(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'open',
                insertText      : 'open(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ord',
                insertText      : 'ord(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'pow',
                insertText      : 'pow(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'print',
                insertText      : 'print(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'property',
                insertText      : 'property(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'range',
                insertText      : 'range(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'repr',
                insertText      : 'repr(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'reversed',
                insertText      : 'reversed(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'round',
                insertText      : 'round(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'set',
                insertText      : 'set(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'setattr',
                insertText      : 'setattr(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'slice',
                insertText      : 'slice(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'sorted',
                insertText      : 'sorted(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'str',
                insertText      : 'str(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'sum',
                insertText      : 'sum(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'tuple',
                insertText      : 'tuple(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'type',
                insertText      : 'type(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'vars',
                insertText      : 'vars(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'zip',
                insertText      : 'zip(${1})',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // python变量
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : '__main__',
                insertText      : '__main__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__module__',
                insertText      : '__module__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__name__',
                insertText      : '__name__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__doc__',
                insertText      : '__doc__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__package__',
                insertText      : '__package__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__loader__',
                insertText      : '__loader__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__dict__',
                insertText      : '__dict__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__class__',
                insertText      : '__class__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__base__',
                insertText      : '__base__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__bases__',
                insertText      : '__bases__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__members__',
                insertText      : '__members__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__methods__',
                insertText      : '__methods__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__mro__',
                insertText      : '__mro__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__slot__',
                insertText      : '__slot__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__globals__',
                insertText      : '__globals__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__code__',
                insertText      : '__code__',
                kind            : monaco.languages.CompletionItemKind.Variable
            },


        ////////////////////////////////////////////////////////////////////////////////////////
        // 策略函数
        //////////////////////////////////////////////////////////////////////////////////////// 
            {
                label           : 'Date(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'Date(${1})',
                detail          : '# 当前Bar的日期\n' +
                                  '    int Date(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    简写D,返回格式为YYYYMMDD的整数\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    当前Bar对应的日期为2019-03-25，则Date返回值为20190325',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Time(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'Time(${1})',
                detail          : '# 当前Bar的时间\n' +
                                  '    float Time(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    简写T, 返回格式为0.HHMMSS的浮点数\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    当前Bar对应的时间为11:34:21，Time返回值为0.113421\n' +
                                  '    当前Bar对应的时间为09:34:00，Time返回值为0.0934\n' +
                                  '    当前Bar对应的时间为11:34:00，Time返回值为0.1134',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Open(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'Open(${1})',
                detail          : '# 指定合约指定周期的开盘价\n' +
                                  '    array Open(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    简写O, 返回值numpy数组包含截止当前Bar的所有开盘价\n' +
                                  '    Open()[-1] 表示当前Bar开盘价，Open()[-2]表示上一个Bar开盘价，以此类推\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    Open() 获取基准合约的所有开盘价列表\n' +
                                  '    Open(\'ZCE|F|SR|905\', \'M\', 1) 获取白糖905合约1分钟K线的所有开盘价列表',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'High(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'High(${1})',
                detail          : '# 指定合约指定周期的最高价\n' +
                                  '    array High(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号,默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    简写H, Tick时为当时的委托卖价\n' +
                                  '    返回numpy数组，包括截止当前Bar的所有最高价\n' +
                                  '    High(\'ZCE|F|SR|905\', \'M\', 1)[-1] 表示当前Bar最高价，High(\'ZCE|F|SR|905\', \'M\', 1)[-2]表示上一个Bar最高价，以此类推',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Low(contractNo=\'\', klineType=\'\', kLineValue=0)',
                insertText      : 'Low(${1})',
                detail          : '# 指定合约指定周期的最低价\n' +
                                  '    array Low(string contractNo=\'\', char klineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    简写H, Tick时为当时的委托卖价\n' +
                                  '    返回numpy数组，包括截止当前Bar的所有最低价\n' +
                                  '    Low()[-1] 表示当前Bar最低价，Low()[-2]表示上一个Bar最低价，以此类推',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Close(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'Close(${1})',
                detail          : '# 指定合约指定周期的收盘价\n' +
                                  '    array Close(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    简写C, 返回numpy数组，包括截止当前Bar的所有收盘价\n' +
                                  '    Close()[-1] 表示当前Bar收盘价，Close()[-2]表示上一个Bar收盘价，以此类推',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'OpenD(daysAgo=0, contractNo=\'\')',
                insertText      : 'OpenD(${1})',
                detail          : '# 指定合约指定周期N天前的开盘价\n' +
                                  '    float OpenD(int daysAgo=0, string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    daysAgo 第几天前，默认值为0，即当天\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, \'D\', 1)方法订阅contractNo合约的日线信息；\n' +
                                  '    若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    OpenD(3，\'ZCE|F|SR|905\') 获取白糖905合约3天前的开盘价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CloseD(daysAgo=0, contractNo=\'\')',
                insertText      : 'CloseD(${1})',
                detail          : '# 指定合约指定周期N天前的收盘价\n' +
                                  '    float CloseD(int daysAgo=0, string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    daysAgo 第几天前，默认值为0，即当天\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, \'D\', 1)方法订阅contractNo合约的日线信息；\n' +
                                  '    若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    CloseD(3，\'ZCE|F|SR|905\') 获取白糖905合约3天前的收盘价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HighD(daysAgo=0, contractNo=\'\')',
                insertText      : 'HighD(${1})',
                detail          : '# 指定合约指定周期N天前的最高价\n' +
                                  '    float HighD(int daysAgo=0, string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    daysAgo 第几天前，默认值为0，即当天\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, \'D\', 1)方法订阅contractNo合约的日线信息；\n' +
                                  '    若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    HighD(3，\'ZCE|F|SR|905\') 获取白糖905合约3天前的最高价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LowD(daysAgo=0, contractNo=\'\')',
                insertText      : 'LowD(${1})',
                detail          : '# 指定合约指定周期N天前的最低价\n' +
                                  '    float LowD(int daysAgo=0, string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    daysAgo 第几天前，默认值为0，即当天\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    使用该函数前请确保在策略的initial方法中使用SetBarInterval(contractNo, \'D\', 1)方法订阅contractNo合约的日线信息；\n' +
                                  '    若daysAgo超过了订阅合约contractNo日线数据的样本数量，则返回为-1。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    LowD(3，\'ZCE|F|SR|905\') 获取白糖905合约3天前的最低价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Vol(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'Vol(${1})',
                detail          : '# 指定合约指定周期的成交量\n' +
                                  '    array Vol(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    简写V, 返回numpy数组，包括截止当前Bar的所有成交量\n' +
                                  '    Vol()[-1] 表示当前Bar成交量，Vol()[-2]表示上一个Bar成交量，以此类推',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'OpenInt(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'OpenInt(${1})',
                detail          : '# 指定合约指定周期的持仓量\n' +
                                  '    numpy.array OpenInt(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回numpy数组，包括截止当前Bar的所有持仓量\n' +
                                  '    OpenInt()[-1] 表示当前Bar持仓量，OpenInt()[-2]表示上一个Bar持仓量，以此类推',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TradeDate(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'TradeDate(${1})',
                detail          : '# 指定合约当前Bar的交易日\n' +
                                  '    int TradeDate(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回格式为YYYYMMDD的整数\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    当前Bar对用的日期为2019-03-25，则Date返回值为20190325',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarCount(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'BarCount(${1})',
                detail          : '# 指定合约Bar的总数\n' +
                                  '    int BarCount(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回值为整型',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CurrentBar(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'CurrentBar(${1})',
                detail          : '# 指定合约当前Bar的索引值\n' +
                                  '    int CurrentBar(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    第一个Bar返回值为0，其他Bar递增\n' +
                                  '    当无数据时，不存在当前Bar，返回-1',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarStatus(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'BarStatus(${1})',
                detail          : '# 指定合约当前Bar的状态值\n' +
                                  '    int BarStatus(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回值整型, 0表示第一个Bar,1表示中间普通Bar,2表示最后一个Bar',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HistoryDataExist(contractNo=\'\', kLineType=\'\', kLineValue=0)',
                insertText      : 'HistoryDataExist(${1})',
                detail          : '# 指定合约的历史数据是否有效\n' +
                                  '    bool HistoryDataExist(string contractNo=\'\', char kLineType=\'\', int kLineValue=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认基准合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回Bool值，有效返回True，否则返回False',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HisData(enum dataType, enum kLineType=\'\', kLineValue=0, contractNo=\'\', maxLength=100)',
                insertText      : 'HisData(${1})',
                detail          : '# 获取各种历史数据数组\n' +
                                  '    numpy.array HisData(enum dataType, enum kLineType=\'\', int kLineValue=0, string contractNo=\'\', int maxLength=100)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    dataType 指定历史数据的种类，可选的枚举函数和相应含义为：\n' +
                                  '    Enum_Data_Close         : 收盘价\n' +
                                  '    Enum_Data_Open          : 开盘价\n' +
                                  '    Enum_Data_High          : 最高价\n' +
                                  '    Enum_Data_Low           : 最低价\n' +
                                  '    Enum_Data_Median        : 中间价\n' +
                                  '    Enum_Data_Typical       : 标准价\n' +
                                  '    Enum_Data_Weighted      : 加权收盘价\n' +
                                  '    Enum_Data_Vol           : 成交量\n' +
                                  '    Enum_Data_Opi           : 持仓量\n' +
                                  '    Enum_Data_Time          : K线时间\n' +
                                  '    \n' +
                                  '    kLineType 指定周期类型，可选的枚举函数和相应含义为：\n' +
                                  '    Enum_Period_Tick        : 周期类型_分笔\n' +
                                  '    Enum_Period_Second      : 周期类型_秒线\n' +
                                  '    Enum_Period_Min         : 周期类型_分钟\n' +
                                  '    Enum_Period_Day         : 周期类型_日线\n' +
                                  '    \n' +
                                  '    kLineValue 周期数， 如：5分钟线，周期数就是5；50秒线，周期数为50\n' +
                                  '    contractNo 合约编号, 为空时取当前合约\n' +
                                  '    maxLength 定返回历史数据数组的最大长度，默认值为100\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回numpy数组，包括截止当前Bar的最多maxLength个指定的种类的历史数据\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    closeList = HisData(Enum_Data_Close(), Enum_Period_Min(), 5, \"ZCE|F|SR|906\", 1000) # 获取合约ZCE|F|SR|906包含当前Bar在内的之前1000个5分钟线的收盘价\n' +
                                  '    closeList[-1] # 当前Bar的收盘价\n' +
                                  '    closeList[-2] # 上一个Bar的收盘价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HisBarsInfo(contractNo=\'\', kLineType=\'\', kLineValue=0, maxLength=None)',
                insertText      : 'HisBarsInfo(${1})',
                detail          : '# 获取最多maxLength根指定类型的历史K线详细数据\n' +
                                  '    list HisBarsInfo(string contractNo=\'\', char kLineType=\'\', int kLineValue=0, int maxLength=None)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 为空时取当前合约\n' +
                                  '    kLineType K线类型，可选值请参阅周期类型枚举函数\n' +
                                  '    kLineValue K线周期\n' +
                                  '    maxLength 定返回历史数据数组的最大长度，默认值为所有K线数据\n' +
                                  '    若contractNo, kLineType, kLineValue同时不填，则取用于展示的合约及相应的K线类型和周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回列表，包括截止当前Bar的最多maxLength个K线的历史数据\n' +
                                  '    列表中以字典的形式保存每个K线的数据，字典中每个键值的含义如下:\n' +
                                  '    ContractNo 合约编号，如\'NYMEX|F|CL|1907\'\n' +
                                  '    DateTimeStamp 更新时间，如20190521130800000\n' +
                                  '    KLineIndex K线索引，如1\n' +
                                  '    KLineQty K线成交量，如18\n' +
                                  '    TotalQty 总成交量，如41401\n' +
                                  '    KLineSlice K线周期， 如1\n' +
                                  '    KLineType K线周期，如\'M\'\n' +
                                  '    OpeningPrice 开盘价， 如63.5\n' +
                                  '    LastPrice 收盘价，如63.49\n' +
                                  '    SettlePrice 结算价，如63.21\n' +
                                  '    HighPrice 最高价，如63.5\n' +
                                  '    LowPrice 最低价， 如63.49\n' +
                                  '    PositionQty 总持仓，如460816\n' +
                                  '    TradeDate\' 交易日期，如20190521\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    barList = HisBarsInfo(\"ZCE|F|SR|906\", Enum_Period_Min(), 5, 1000) # 获取合约ZCE|F|SR|906包含当前Bar在内的之前1000个历史5分钟K线的数据\n' +
                                  '    barInfo = barList[-1] # 当前Bar的详细信息',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_UpdateTime(contractNo=\'\')',
                insertText      : 'Q_UpdateTime(${1})',
                detail          : '# 获取指定合约即时行情的更新时间\n' +
                                  '    string Q_UpdateTime(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认当前合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回格式为\"YYYYMMDDHHMMSSmmm\"的字符串，\n' +
                                  '    若指定合约即时行情的更新时间为2019-05-21 10:07:46.000，则该函数放回为20190521100746000',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_AskPrice(contractNo=\'\', level=1)',
                insertText      : 'Q_AskPrice(${1})',
                detail          : '# 合约最优卖价\n' +
                                  '    float Q_AskPrice(string contractNo=\'\', int level=1)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认当前合约;level 档位数,默认1档\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 可获取指定合约,指定深度的最优卖价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_AskPriceFlag(contractNo=\'\')',
                insertText      : 'Q_AskPriceFlag(${1})',
                detail          : '# 卖盘价格变化标志\n' +
                                  '    int Q_AskPriceFlag(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认当前合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，1为上涨，-1为下跌，0为不变',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_AskVol(contractNo=\'\', level=1)',
                insertText      : 'Q_AskVol(${1})',
                detail          : '# 合约最优卖量\n' +
                                  '    float Q_AskVol(string contractNo=\'\', int level=1)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认当前合约;level 档位数,默认1档\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 可获取指定合约,指定深度的最优卖量',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_AvgPrice(contractNo=\'\')',
                insertText      : 'Q_AvgPrice(${1})',
                detail          : '# 当前合约的实时均价\n' +
                                  '    float Q_AvgPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认当前合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数，返回实时均价即结算价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_BidPrice(contractNo=\'\', level=1)',
                insertText      : 'Q_BidPrice(${1})',
                detail          : '# 合约最优买价\n' +
                                  '    float Q_BidPrice(string contractNo=\'\', int level=1)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认当前合约;level 档位数,默认1档\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 可获取指定合约,指定深度的最优买价',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_AskPriceFlag(contractNo=\'\')',
                insertText      : 'Q_BidPriceFlag(${1})',
                detail          : '# 买盘价格变化标志\n' +
                                  '    int Q_AskPriceFlag(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号,  默认当前合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，1为上涨，-1为下跌，0为不变',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_BidVol(contractNo=\'\', level=1)',
                insertText      : 'Q_BidVol(${1})',
                detail          : '# 合约最优买量\n' +
                                  '    float Q_BidVol(string contractNo=\'\', int level=1)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号, 默认当前合约;level 档位数,默认1档\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 可获取指定合约,指定深度的最优买量',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Close(contractNo=\'\')',
                insertText      : 'Q_Close(${1})',
                detail          : '# 当日收盘价，未收盘则取昨收盘\n' +
                                  '    float Q_Close(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号,默认当前合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_High(contractNo=\'\')',
                insertText      : 'Q_High(${1})',
                detail          : '# 当日最高价\n' +
                                  '    float Q_High(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_HisHigh(contractNo=\'\')',
                insertText      : 'Q_HisHigh(${1})',
                detail          : '# 历史最高价\n' +
                                  '    float Q_HisHigh(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_HisLow(contractNo=\'\')',
                insertText      : 'Q_HisLow(${1})',
                detail          : '# 历史最低价\n' +
                                  '    float Q_HisLow(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_InsideVol(contractNo=\'\')',
                insertText      : 'Q_InsideVol(${1})',
                detail          : '# 内盘量\n' +
                                  '    float Q_InsideVol(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 买入价成交为内盘',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Last(contractNo=\'\')',
                insertText      : 'Q_Last(${1})',
                detail          : '# 最新价\n' +
                                  '    float Q_Last(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_LastDate(contractNo=\'\')',
                insertText      : 'Q_LastDate(${1})',
                detail          : '# 最新成交日期\n' +
                                  '    int Q_LastDate(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回当前公式应用商品的最新成交日期，格式为YYYYMMDD整数表示的日期。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_LastTime(contractNo=\'\')',
                insertText      : 'Q_LastTime(${1})',
                detail          : '# 最新成交时间\n' +
                                  '    float Q_LastTime(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回当前公式应用商品的最新成交时间，以格式为0.HHMMSSmmm浮点数表示的时间。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_LastVol(contractNo=\'\')',
                insertText      : 'Q_LastVol(${1})',
                detail          : '# 现手\n' +
                                  '    float Q_LastVol(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数，单位为手',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Low(contractNo=\'\')',
                insertText      : 'Q_Low(${1})',
                detail          : '# 当日最低价\n' +
                                  '    float Q_Low(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_LowLimit(contractNo=\'\')',
                insertText      : 'Q_LowLimit(${1})',
                detail          : '# 当日跌停板价\n' +
                                  '    float Q_LowLimit(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Open(contractNo=\'\')',
                insertText      : 'Q_Open(${1})',
                detail          : '# 当日开盘价\n' +
                                  '    float Q_Open(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_OpenInt(contractNo=\'\')',
                insertText      : 'Q_OpenInt(${1})',
                detail          : '# 持仓量\n' +
                                  '    float Q_OpenInt(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 单位为手',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_OpenIntFlag(contractNo=\'\')',
                insertText      : 'Q_OpenIntFlag(${1})',
                detail          : '# 持仓量变化标志\n' +
                                  '    int  Q_OpenIntFlag(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型, 1为增加，-1为下降，0为不变',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_OutsideVol(contractNo=\'\')',
                insertText      : 'Q_OutsideVol(${1})',
                detail          : '# 外盘量\n' +
                                  '    float Q_OutsideVol(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数，卖出价成交为外盘',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_PreOpenInt(contractNo=\'\')',
                insertText      : 'Q_PreOpenInt(${1})',
                detail          : '# 昨持仓量\n' +
                                  '    float Q_PreOpenInt(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_PreSettlePrice(contractNo=\'\')',
                insertText      : 'Q_PreSettlePrice(${1})',
                detail          : '# 昨结算\n' +
                                  '    float Q_PreSettlePrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_PriceChg(contractNo=\'\')',
                insertText      : 'Q_PriceChg(${1})',
                detail          : '# 当日涨跌\n' +
                                  '    float Q_PriceChg(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_PriceChgRadio(contractNo=\'\')',
                insertText      : 'Q_PriceChgRadio(${1})',
                detail          : '# 当日涨跌幅\n' +
                                  '    float Q_PriceChgRadio(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_TodayEntryVol(contractNo=\'\')',
                insertText      : 'Q_TodayEntryVol(${1})',
                detail          : '# 当日开仓量\n' +
                                  '    float Q_TodayEntryVol(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_TodayExitVol(contractNo=\'\')',
                insertText      : 'Q_TodayExitVol(${1})',
                detail          : '# 当日平仓量\n' +
                                  '    float Q_TodayExitVol(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_TotalVol(contractNo=\'\')',
                insertText      : 'Q_TotalVol(${1})',
                detail          : '# 当日成交量\n' +
                                  '    float Q_TotalVol(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_TurnOver(contractNo=\'\')',
                insertText      : 'Q_TurnOver(${1})',
                detail          : '# 当日成交额\n' +
                                  '    float Q_TurnOver(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_UpperLimit(contractNo=\'\')',
                insertText      : 'Q_UpperLimit(${1})',
                detail          : '# 当日涨停板价\n' +
                                  '    float Q_UpperLimit(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_TheoryPrice(contractNo=\'\')',
                insertText      : 'Q_TheoryPrice(${1})',
                detail          : '# 当日期权理论价\n' +
                                  '    float Q_TheoryPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 不存在时返回None',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Sigma(contractNo=\'\')',
                insertText      : 'Q_Sigma(${1})',
                detail          : '# 当日期权波动率\n' +
                                  '    float Q_Sigma(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 不存在时返回None',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Delta(contractNo=\'\')',
                insertText      : 'Q_Delta(${1})',
                detail          : '# 当日期权Delta\n' +
                                  '    float Q_Delta(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 不存在时返回None',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Gamma(contractNo=\'\')',
                insertText      : 'Q_Gamma(${1})',
                detail          : '# 当日期权Gamma\n' +
                                  '    float Q_Gamma(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 不存在时返回None',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Vega(contractNo=\'\')',
                insertText      : 'Q_Vega(${1})',
                detail          : '# 当日期权Vega\n' +
                                  '    float Q_Vega(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 不存在时返回None',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Theta(contractNo=\'\')',
                insertText      : 'Q_Theta(${1})',
                detail          : '# 当日期权Theta\n' +
                                  '    float Q_Theta(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 不存在时返回None',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Q_Rho(contractNo=\'\')',
                insertText      : 'Q_Rho(${1})',
                detail          : '# 当日期权Rho\n' +
                                  '    float Q_Rho(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数, 不存在时返回None',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'QuoteDataExist(contractNo=\'\')',
                insertText      : 'QuoteDataExist(${1})',
                detail          : '# 行情数据是否有效\n' +
                                  '    Bool QuoteDataExist(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回Bool值，数据有效返回True，否则False',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CalcTradeDate(contractNo=\'\', dateTimeStamp=0)',
                insertText      : 'CalcTradeDate(${1})',
                detail          : '# 计算指定合约，指定时间戳所属的交易日\n' +
                                  '    int CalcTradeDate(string contractNo=\'\', int dateTimeStamp=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认基准合约\n' +
                                  '    dateTimeStamp  时间戳，默认0\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    正常情况，返回指定合约指定时间戳所属的交易日\n' +
                                  '    当返回值为-1时，表示合约参数有误\n' +
                                  '    当返回值为-2时，表示时间戳参数有误，比如传入非交易时段时间戳\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    CalcTradeDate(dateTimeStamp=20190830110000000)\n' +
                                  '    CalcTradeDate(\'ZCE|F|SR|001\', 20190830110000000)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Buy(share=0, price=0, contractNo=None, needCover=True, userNo=\'\')',
                insertText      : 'Buy(${1})',
                detail          : '# 产生一个多头建仓操作\n' +
                                  '    Buy(int share=0, float price=0, string contractNo=None, bool needCover = True, string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    share 买入数量，为整型值，默认为0；\n' +
                                  '    price 买入价格，为浮点数，默认为0；\n' +
                                  '    contract 合约代码，为字符串，默认使用基准合约；\n' +
                                  '    needCover 是否先清掉方向持仓，默认为True；\n' +
                                  '    userNo 用户编号，为字符串，默认使用界面选定用户编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    产生一个多头建仓操作，无返回值。\n' +
                                  '    该函数仅用于多头建仓，其处理规则如下：\n' +
                                  '    如果当前持仓状态为持平，该函数按照参数进行多头建仓。\n' +
                                  '    如果当前持仓状态为空仓，该函数平掉所有空仓，同时按照参数进行多头建仓，两个动作同时发出。\n' +
                                  '    如果当前持仓状态为多仓，该函数将继续建仓，但具体是否能够成功建仓要取决于系统中关于连续建仓的设置，以及资金，最大持仓量等限制。\n' +
                                  '    当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。\n' +
                                  '    例如：当前k线有效价格为50-100，用buy(1,10)发单，委托价将以50发单。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    在当前没有持仓或者持有多头仓位的情况下：\n' +
                                  '    Buy(50,10.2) 表示用10.2的价格买入50张合约。\n' +
                                  '    Buy(10,Close) 表示用当前Bar收盘价买入10张合约，马上发送委托。\n' +
                                  '    Buy(5,0) 表示用现价买入5张合约，马上发送委托。\n' +
                                  '    Buy(0,0) 表示用现价按交易设置中设置的手数,马上发送委托。\n' +
                                  '    \n' +
                                  '    在当前持有空头仓位的情况下：\n' +
                                  '    Buy(10,Close) 表示平掉所有空仓，并用当前Bar收盘价买入10张合约，马上发送委托。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BuyToCover(share=0, price=0, contractNo=None, userNo=\'\', coverFlag=\'A\')',
                insertText      : 'BuyToCover(${1})',
                detail          : '# 产生一个空头平仓操作\n' +
                                  '    BuyToCover(int share=0, float price=0, string contractNo=None, string userNo=\'\', char coverFlag = \'A\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    share 买入数量，为整型值，默认为0；\n' +
                                  '    price 买入价格，为浮点数，默认为0；\n' +
                                  '    contract 合约代码，为字符串，默认使用基准合约；\n' +
                                  '    userNo 用户编号，为字符串，默认使用界面选定用户编号。\n' +
                                  '    coverFlag 平今平昨标志（此参数仅对SHFE和INE有效）\n' +
                                  '    默认设置为\'A\'自适应(先平昨再平今)\n' +
                                  '    若平昨，则需设置为\'C\'\n' +
                                  '    若平今，则需设置为\'T\'\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    产生一个空头平仓操作，无返回值。\n' +
                                  '    该函数仅用于空头平仓，其处理规则如下：\n' +
                                  '    如果当前持仓状态为持平，该函数不执行任何操作。\n' +
                                  '    如果当前持仓状态为多仓，该函数不执行任何操作。\n' +
                                  '    如果当前持仓状态为空仓，如果此时Share使用默认值，该函数将平掉所有空仓，达到持平的状态，否则只平掉参数Share的空仓。\n' +
                                  '    当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。\n' +
                                  '    例如：当前k线有效价格为50-100，用BuyToCover(1,10)发单，委托价将以50发单。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    在持有空头仓位的情况下：\n' +
                                  '    BuyToCover(50,10.2) 表示用10.2的价格空头买入50张合约。\n' +
                                  '    BuyToCover(10,Close) 表示用当前Bar收盘价空头买入10张合约，马上发送委托。\n' +
                                  '    BuyToCover(5,0) 表示用现价空头买入5张合约)，马上发送委托。\n' +
                                  '    BuyToCover(0,0) 表示用现价按交易设置中的设置,马上发送委托。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Sell(share=0, price=0, contractNo=None, userNo=\'\', coverFlag=\'A\')',
                insertText      : 'Sell(${1})',
                detail          : '# 产生一个多头平仓操作\n' +
                                  '    Sell(int share=0, float price=0, string contractNo=None, string userNo=\'\', char coverFlag = \'A\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    share 买入数量，为整型值，默认为0；\n' +
                                  '    price 买入价格，为浮点数，默认为0；\n' +
                                  '    contract 合约代码，为字符串，默认使用基准合约；\n' +
                                  '    userNo 用户编号，为字符串，默认使用界面选定用户编号。\n' +
                                  '    coverFlag 平今平昨标志（此参数仅对SHFE和INE有效）\n' +
                                  '    默认设置为\'A\'自适应(先平昨再平今)\n' +
                                  '    若平昨，则需设置为\'C\'\n' +
                                  '    若平今，则需设置为\'T\'\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    产生一个多头平仓操作，无返回值。\n' +
                                  '    该函数仅用于多头平仓，其处理规则如下：\n' +
                                  '    如果当前持仓状态为持平，该函数不执行任何操作。\n' +
                                  '    如果当前持仓状态为空仓，该函数不执行任何操作。\n' +
                                  '    如果当前持仓状态为多仓，如果此时Share使用默认值，该函数将平掉所有多仓，达到持平的状态，否则只平掉参数Share的多仓。\n' +
                                  '    当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。\n' +
                                  '    例如：当前k线有效价格为50-100，用sell(1,10)发单，委托价将以50发单。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    在持有多头仓位的情况下：\n' +
                                  '    Sell(50,10.2) 表示用10.2的价格卖出50张合约。\n' +
                                  '    Sell(10,Close) 表示用当前Bar收盘价卖出10张合约，马上发送委托。\n' +
                                  '    Sell(5,0) 表示用现价卖出5张合约，马上发送委托。\n' +
                                  '    Sell(0,0) 表示用现价按交易设置中的设置,马上发送委托。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SellShort(share=0, price=0, contractNo=None, needCover=True, userNo=\'\')',
                insertText      : 'SellShort(${1})',
                detail          : '# 产生一个空头建仓操作\n' +
                                  '    SellShort(int share=0, float price=0, string contractNo=None, bool needCover = True, string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    share 买入数量，为整型值，默认为0；\n' +
                                  '    price 买入价格，为浮点数，默认为0；\n' +
                                  '    contract 合约代码，为字符串，默认使用基准合约；\n' +
                                  '    needCover 是否先清掉方向持仓，默认为True；\n' +
                                  '    userNo 用户编号，为字符串，默认使用界面选定用户编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    产生一个空头建仓操作，无返回值。\n' +
                                  '    该函数仅用于空头建仓，其处理规则如下：\n' +
                                  '    如果当前持仓状态为持平，该函数按照参数进行空头建仓。\n' +
                                  '    如果当前持仓状态为多仓，该函数平掉所有多仓，同时按照参数进行空头建仓，两个动作同时发出\n' +
                                  '    如果当前持仓状态为空仓，该函数将继续建仓，但具体是否能够成功建仓要取决于系统中关于连续建仓的设置，以及资金，最大持仓量等限制。\n' +
                                  '    当委托价格超出k线的有效范围，在历史数据上，将会取最接近的有效价格发单；在实盘中，将会按照实际委托价格发单。\n' +
                                  '    例如：当前k线有效价格为50-100，用SellShort(1,10)发单，委托价将以50发单。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    在没有持仓或者持有空头持仓的情况下：\n' +
                                  '    SellShort(50,10.2) 表示用10.2的价格空头卖出50张合约。\n' +
                                  '    SellShort(10,Close) 表示用当前Bar收盘价空头卖出10张合约，马上发送委托。\n' +
                                  '    SellShort(5,0) 表示用现价空头卖出5张合约，马上发送委托。\n' +
                                  '    SellShort(0,0) 表示用现价按交易设置中设置的手数,马上发送委托。\n' +
                                  '    在MarketPosition=1的情况下：（当前持有多头持仓）\n' +
                                  '    SellShort(10,Close) 表示平掉所有多头仓位，并用当前Bar收盘价空头卖出10张合约，马上发送委托。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'StartTrade()',
                insertText      : 'StartTrade()',
                detail          : '# 开启实盘交易。\n' +
                                  '    StartTrade()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在策略运行时，使用StopTrade可以暂时停止策略向实盘发单，通过该方法可以开启策略向实盘发单的功能。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'StopTrade()',
                insertText      : 'StopTrade()',
                detail          : '# 暂停实盘交易。\n' +
                                  '    StopTrade()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在策略运行时，使用StopTrade可以暂时停止策略向实盘发单。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'IsTradeAllowed()',
                insertText      : 'IsTradeAllowed()',
                detail          : '# 是否允许实盘交易。\n' +
                                  '    bool IsTradeAllowed()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获取策略是否可以向实盘发单的布尔值，策略实盘运行时并且允许向实盘发单返回True，否则返回False。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'BarInterval()',
                insertText      : 'BarInterval()',
                detail          : '# 返回界面合约图表K线周期数值\n' +
                                  '    int BarInterval()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回界面图表K线周期数值，通常和BarType一起使用进行数据周期的判别\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    当前数据周期为1日线，BarInterval等于1；\n' +
                                  '    当前数据周期为22日线，BarInterval等于22；\n' +
                                  '    当前数据周期为60分钟线，BarInterval等于60；\n' +
                                  '    当前数据周期为1TICK线，BarInterval等于1；br>当前数据周期为5000量线，BarInterval等于5000。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'BarType()',
                insertText      : 'BarType()',
                detail          : '# 返回界面合约K线图表周期类型字符\n' +
                                  '    char BarType()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回值为字符，通常和BarInterval一起使用进行数据周期的判别\n' +
                                  '    返回值如下定义：\n' +
                                  '    T 分笔\n' +
                                  '    S 秒线\n' +
                                  '    M 分钟\n' +
                                  '    D 日线\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    当前数据周期为22日线，BarType等于D；\n' +
                                  '    当前数据周期为60分钟线，BarType等于M；\n' +
                                  '    当前数据周期为1TICK线，BarType等于T。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'BidAskSize(contractNo=\'\')',
                insertText      : 'BidAskSize(${1})',
                detail          : '# 买卖盘个数\n' +
                                  '    int BidAskSize(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo: 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    郑商所白糖的买卖盘个数为5个，因此其BidAskSize等于5；\n' +
                                  '    郑商所棉花的买卖盘个数为1个，因此其BidAskSize等于1。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CanTrade(contractNo=\'\')',
                insertText      : 'CanTrade(${1})',
                detail          : '# 合约是否支持交易\n' +
                                  '    Bool CanTrade(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo: 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回Bool值，支持返回True，否则返回False',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ContractUnit(contractNo=\'\')',
                insertText      : 'ContractUnit(${1})',
                detail          : '# 每张合约包含的基本单位数量, 即每手乘数\n' +
                                  '    int ContractUnit(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo: 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，1张合约包含多少标底物。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ExchangeName(contractNo=\'\')',
                insertText      : 'ExchangeName(${1})',
                detail          : '# 合约对应交易所名称\n' +
                                  '    string ExchangeName(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo: 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    郑商所下各合约的交易所名称为：\"郑州商品交易所\"',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ExchangeTime(contractNo)',
                insertText      : 'ExchangeTime(${1})',
                detail          : '# 交易所时间\n' +
                                  '    string ExchangeTime(string contractNo)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    exchangeNo: 交易所编号，例如\"ZCE\",\"DCE\",\"SHFE\",\"CFFEX\",\"INE\"\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串 \"2019-07-05 22:11:00\"\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    ExchangeTime(\'ZCE\')',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ExchangeStatus(exchangeNo)',
                insertText      : 'ExchangeStatus(${1})',
                detail          : '# 交易所状态\n' +
                                  '    string ExchangeStatus(string exchangeNo)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    exchangeNo: 交易所编号，例如\"ZCE\",\"DCE\",\"SHFE\",\"CFFEX\",\"INE\"\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符\n' +
                                  '    \'N\'   未知状态\n' +
                                  '    \'I\'   正初始化\n' +
                                  '    \'R\'   准备就绪\n' +
                                  '    \'0\'   交易日切换\n' +
                                  '    \'1\'   竞价申报\n' +
                                  '    \'2\'   竞价撮合\n' +
                                  '    \'3\'   连续交易\n' +
                                  '    \'4\'   交易暂停\n' +
                                  '    \'5\'   交易闭市\n' +
                                  '    \'6\'   竞价暂停\n' +
                                  '    \'7\'   报盘未连\n' +
                                  '    \'8\'   交易未连\n' +
                                  '    \'9\'   闭市处理\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    ExchangeStatus(\'ZCE\')',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CommodityStatus(commodityNo|string contractNo)',
                insertText      : 'CommodityStatus(${1})',
                detail          : '# 品种或合约交易状态\n' +
                                  '    string CommodityStatus(string commodityNo|string contractNo)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    commodityNo: 品种编号，例如\"ZCE|F|SR\", \"DCE|F|I\"\n' +
                                  '    或者\n' +
                                  '    contractNo: 合约编号，例如\"ZCE|F|SR|001\", \"DCE|F|I|2001\"\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符\n' +
                                  '    \'N\'   未知状态\n' +
                                  '    \'I\'   正初始化\n' +
                                  '    \'R\'   准备就绪\n' +
                                  '    \'0\'   交易日切换\n' +
                                  '    \'1\'   竞价申报\n' +
                                  '    \'2\'   竞价撮合\n' +
                                  '    \'3\'   连续交易\n' +
                                  '    \'4\'   交易暂停\n' +
                                  '    \'5\'   交易闭市\n' +
                                  '    \'6\'   竞价暂停\n' +
                                  '    \'7\'   报盘未连\n' +
                                  '    \'8\'   交易未连\n' +
                                  '    \'9\'   闭市处理\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    CommodityStatus(\'ZCE|F|SR\')',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ExpiredDate(contractNo=\'\')',
                insertText      : 'ExpiredDate(${1})',
                detail          : '# 合约最后交易日\n' +
                                  '    string ExpiredDate(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo: 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'GetSessionCount(contractNo=\'\')',
                insertText      : 'GetSessionCount(${1})',
                detail          : '# 获取交易时间段的个数\n' +
                                  '    int GetSessionCount(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo: 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'GetSessionEndTime(contractNo=\'\', index=0)',
                insertText      : 'GetSessionEndTime(${1})',
                detail          : '# 获取指定交易时间段的结束时间。\n' +
                                  '    float GetSessionEndTime(string contractNo=\'\', int index=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '    index 交易时间段的索引值, 从0开始。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定合约的交易时间段结束时间，格式为0.HHMMSS的浮点数。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    contractNo = \"ZCE|F|SR|905\"\n' +
                                  '    sessionCount = GetSessionCount(contractNo)\n' +
                                  '    for i in range(0, sessionCount-1):\n' +
                                  '    sessionEndTime = GetSessionEndTime(contractNo, i)\n' +
                                  '    \n' +
                                  '    由于合约ZCE|F|TA|908的第三段交易结束时间为11:30:00，\n' +
                                  '    所以GetSessionEndTime(\"ZCE|F|TA|908\", 2)的返回值为0.113',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'GetSessionStartTime(contractNo=\'\', index=0)',
                insertText      : 'GetSessionStartTime(${1})',
                detail          : '# 获取指定交易时间段的开始时间。\n' +
                                  '    float GetSessionStartTime(string contractNo=\'\', int index=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '    index 交易时间段的索引值, 从0开始。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定合约的交易时间段开始时间，格式为0.HHMMSS的浮点数。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'GetNextTimeInfo(contractNo, timeStamp)',
                insertText      : 'GetNextTimeInfo(${1})',
                detail          : '# 获取指定合约指定时间点的下一个时间点及交易状态。\n' +
                                  '    dict GetNextTimeInfo(string contractNo, float timeStamp)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号。\n' +
                                  '    timeStr 指定的时间点，格式为0.HHMMSS。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回时间字典，结构如下：\n' +
                                  '    {\n' +
                                  '    \'Time\' : 0.21,\n' +
                                  '    \'TradeState\' : 3\n' +
                                  '    }\n' +
                                  '    其中Time对应的值表示指定时间timeStamp的下一个时间点，返回指定合约的交易时间段开始时间，格式为0.HHMMSS的浮点数。\n' +
                                  '    TradeState表示对应时间点的交易状态，数据类型为字符，可能出现的值及相应的状态含义如下：\n' +
                                  '    1 : 集合竞价\n' +
                                  '    2 : 集合竞价撮合\n' +
                                  '    3 : 连续交易\n' +
                                  '    4 : 暂停\n' +
                                  '    5 : 闭市\n' +
                                  '    6 : 闭市处理时间\n' +
                                  '    0 : 交易日切换时间\n' +
                                  '    N : 未知状态\n' +
                                  '    I : 正初始化\n' +
                                  '    R : 准备就绪\n' +
                                  '    异常情况返回为空字典：{}\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    GetNextTimeInfo(\'SHFE|F|CU|1907\', 0.22) # 获取22:00:00后下一个时间点的时间和交易状态\n' +
                                  '    获取当前时间下一个时间点的时间和交易状态\n' +
                                  '    import time # 需要在策略头部添加time库\n' +
                                  '    curTime = time.strftime(\'0.%H%M%S\',time.localtime(time.time()))\n' +
                                  '    timeInfoDict = GetNextTimeInfo(\"SHFE|F|CU|1907\", curTime)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TradeSessionBeginTime(contractNo=\'\', tradeDate=0, index=0)',
                insertText      : 'TradeSessionBeginTime(${1})',
                detail          : '# 获取指定合约指定交易日的指定交易时间段的开始时间戳。\n' +
                                  '    int TradeSessionBeginTime(string contractNo=\'\', int tradeDate=0, int index=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '    tradeDate  指定的交易日, 默认0\n' +
                                  '    index 交易时间段的索引值, 从0开始，默认取第一个交易时段。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回时间戳类型, 如20190904213000000',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TradeSessionEndTime(contractNo=\'\', tradeDate=0, index=-1)',
                insertText      : 'TradeSessionEndTime(${1})',
                detail          : '# 获取指定合约指定交易日的指定交易时间段的结束时间戳。\n' +
                                  '    int TradeSessionEndTime(string contractNo=\'\', int tradeDate=0, int index=-1)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '    tradeDate  指定的交易日, 默认0\n' +
                                  '    index 交易时间段的索引值, 从0开始，默认取最后一个交易时段。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回时间戳类型, 如20190904213000000',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CurrentDate()',
                insertText      : 'CurrentDate()',
                detail          : '# 公式处于历史阶段时，返回历史K线当时的日期。处于实时阶段时，返回客户端所在操作系统的日期\n' +
                                  '    int CurrentDate()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    格式为YYMMDD的整数。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    如果当前日期为2019-7-13，CurrentDate返回值为20190713',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'CurrentTime()',
                insertText      : 'CurrentTime()',
                detail          : '# 公式处于历史阶段时，返回历史K线当时的时间。处于实时阶段时，返回客户端所在操作系统的时间\n' +
                                  '    float CurrentTime()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    格式为0.HHMMSS的浮点数。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    如果当前时间为11:34:21，CurrentTime返回值为0.113421。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'TimeDiff(self, datetime1, datetime2)',
                insertText      : 'TimeDiff(${1})',
                detail          : '# 返回两个时间之间的间隔秒数，忽略日期差异\n' +
                                  '    int TimeDiff(self, float datetime1, float datetime2)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    datetime1 输入较早时间\n' +
                                  '    datetime2 输入较晚个时间\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该函数只计算两个时间之间的差值，不考虑两个参数的日期\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    TimeDiff(20190404.104110,20110404.104120);返回两时间相差10秒；\n' +
                                  '    TimeDiff(20190404.1041,20110404.1043);返回两时间相差2分钟，即120秒',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'IsInSession(contractNo=\'\')',
                insertText      : 'IsInSession(${1})',
                detail          : '# 操作系统的当前时间是否为指定合约的交易时间。\n' +
                                  '    bool IsInSession(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基础合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获取操作系统的当前时间，是否为指定合约的交易时间。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    如果当前时间为11:34:21，IsInSession(\"ZCE|F|TA|909\")返回值为False。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MarginRatio(contractNo=\'\')',
                insertText      : 'MarginRatio(${1})',
                detail          : '# 获取合约默认保证金比率\n' +
                                  '    float MarginRatio(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MaxBarsBack()',
                insertText      : 'MaxBarsBack()',
                detail          : '# 最大回溯Bar数\n' +
                                  '    float  MaxBarsBack()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'MaxSingleTradeSize()',
                insertText      : 'MaxSingleTradeSize()',
                detail          : '# 单笔交易限量\n' +
                                  '    int MaxSingleTradeSize()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，单笔交易限量，对于不能交易的商品，返回-1，对于无限量的商品，返回0',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'PriceTick(contractNo=\'\')',
                insertText      : 'PriceTick(${1})',
                detail          : '# 合约最小变动价\n' +
                                  '    int PriceTick(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    沪铝的最小变动价为5，因此其PriceTick等于5',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'OptionStyle(contractNo=\'\')',
                insertText      : 'OptionStyle(${1})',
                detail          : '# 期权类型，欧式还是美式\n' +
                                  '    int OptionStyle(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0为欧式，1为美式',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'OptionType(contractNo=\'\')',
                insertText      : 'OptionType(${1})',
                detail          : '# 返回期权的类型，是看涨还是看跌期权\n' +
                                  '    int OptionType(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0为看涨，1为看跌， -1为异常。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PriceScale(contractNo=\'\')',
                insertText      : 'PriceScale(${1})',
                detail          : '# 合约价格精度\n' +
                                  '    float PriceScale(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    上期沪金的报价精确到小数点2位，则PriceScale为1/100，PriceScale的返回值为0.01',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'RelativeSymbol()',
                insertText      : 'RelativeSymbol()',
                detail          : '# 关联合约\n' +
                                  '    string RelativeSymbol()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串\n' +
                                  '    主连或者近月合约，返回具体的某个月份的合约\n' +
                                  '    期权返回标的合约\n' +
                                  '    套利返回单腿合约，以逗号分隔\n' +
                                  '    其他，返回空字符串\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    \"ZCE|O|SR|905C5000\"白糖期权的关联合约为\"ZCE|F|SR|905\"\n' +
                                  '    \"SPD|m|OI/Y|001|001\"菜油豆油价比的关联合约为\"ZCE|F|OI|001,DCE|F|Y|001\"',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'StrikePrice()',
                insertText      : 'StrikePrice()',
                detail          : '# 获取期权行权价\n' +
                                  '    float StrikePrice()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回浮点数',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'Symbol()',
                insertText      : 'Symbol()',
                detail          : '# 获取展示合约，即基准合约的编号\n' +
                                  '    string Symbol()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    期货、现货、指数: <EXG>|<TYPE>|<ROOT>|<YEAR><MONTH>[DAY]\n' +
                                  '    \n' +
                                  '    期权            : <EXG>|<TYPE>|<ROOT>|<YEAR><MONTH>[DAY]<CP><STRIKE>\n' +
                                  '    \n' +
                                  '    跨期套利        : <EXG>|<TYPE>|<ROOT>|<YEAR><MONTH>[DAY]|<YEAR><MONTH>[DAY]\n' +
                                  '    \n' +
                                  '    跨品种套利      : <EXG>|<TYPE>|<ROOT&ROOT>|<YEAR><MONTH>[DAY]\n' +
                                  '    \n' +
                                  '    极星跨期套利    : <EXG>|s|<ROOT>|<YEAR><MONTH>[DAY]|<YEAR><MONTH>[DAY]\n' +
                                  '    \n' +
                                  '    极星跨品种套利  : <EXG>|m|<ROOT-ROOT>|<YEAR><MONTH>|<YEAR><MONTH>\n' +
                                  '    \n' +
                                  '    极星现货期货套利: <EXG>|p|<ROOT-ROOT>||<YEAR><MONTH>\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    \"ZCE|F|SR|001\", \"ZCE|O|SR|001C5000\"',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'SymbolName(contractNo=\'\')',
                insertText      : 'SymbolName(${1})',
                detail          : '# 获取合约名称\n' +
                                  '    string SymbolName(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    \"ZCE|F|SR|001\"的合约名称为\"白糖001\"',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SymbolType(contractNo=\'\')',
                insertText      : 'SymbolType(${1})',
                detail          : '# 获取合约所属的品种编号\n' +
                                  '    string SymbolType(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    \"ZCE|F|SR|001\"的品种编号为\"ZCE|F|SR\"',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'GetTrendContract(contractNo=\"\")',
                insertText      : 'GetTrendContract(${1})',
                detail          : '# 获取商品主连/近月对应的合约\n' +
                                  '    string GetTrendContract(string contractNo=\"\")\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 取商品主连/近月编号，为空时，取基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    GetTrendContract(\'DCE|Z|I|MAIN\') 的返回为\"DCE|F|I|1909\"\n' +
                                  '    GetTrendContract(\'DCE|Z|I|NEARBY\') 的返回为\"DCE|F|I|1907\"',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'AvgEntryPrice(contractNo=\'\')',
                insertText      : 'AvgEntryPrice(${1})',
                detail          : '# 获得当前持仓指定合约的平均建仓价格。\n' +
                                  '    float AvgEntryPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarsSinceEntry(contractNo=\'\')',
                insertText      : 'BarsSinceEntry(${1})',
                detail          : '# 获得当前持仓中指定合约的第一个建仓位置到当前位置的Bar计数。\n' +
                                  '    int BarsSinceEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓指定合约的第一个建仓位置到当前位置的Bar计数，返回值为整型。\n' +
                                  '    只有当MarketPosition != 0时，即有持仓的状况下，该函数才有意义，否则返回-1。\n' +
                                  '    注意：在开仓Bar上为0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarsSinceExit(contractNo=\'\')',
                insertText      : 'BarsSinceExit(${1})',
                detail          : '# 获得当前持仓中指定合约的最近平仓位置到当前位置的Bar计数。\n' +
                                  '    int BarsSinceExit(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓指定合约的最近平仓位置到当前位置的Bar计数，返回值为整型。\n' +
                                  '    若从未平过仓，则返回-1。\n' +
                                  '    注意：在平仓Bar上为0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarsSinceLastEntry(contractNo=\'\')',
                insertText      : 'BarsSinceLastEntry(${1})',
                detail          : '# 获得当前持仓的最后一个建仓位置到当前位置的Bar计数。\n' +
                                  '    int BarsSinceLastEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓指定合约的最后一个建仓位置到当前位置的Bar计数，返回值为整型。\n' +
                                  '    若当前策略持仓为0，则返回-1。\n' +
                                  '    注意：在建仓Bar上为0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarsSinceLastBuyEntry(contractNo=\'\')',
                insertText      : 'BarsSinceLastBuyEntry(${1})',
                detail          : '# 获得当前持仓的最后一个Buy建仓位置到当前位置的Bar计数。\n' +
                                  '    int BarsSinceLastBuyEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓指定合约的最后一个Buy建仓位置到当前位置的Bar计数，返回值为整型。\n' +
                                  '    若当前策略持仓为0，则返回-1。\n' +
                                  '    注意：在建仓Bar上为0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarsSinceLastSellEntry(contractNo=\'\')',
                insertText      : 'BarsSinceLastSellEntry(${1})',
                detail          : '# 获得当前持仓的最后一个Sell建仓位置到当前位置的Bar计数。\n' +
                                  '    int BarsSinceLastSellEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓指定合约的最后一个Sell建仓位置到当前位置的Bar计数，返回值为整型。\n' +
                                  '    若当前策略持仓为0，则返回-1。\n' +
                                  '    注意：在建仓Bar上为0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarsSinceToday(contractNo=\'\', kLineType=\'\', kLineValue=\'\')',
                insertText      : 'BarsSinceToday(${1})',
                detail          : '# 获得当天的第一根Bar到当前的Bar个数。\n' +
                                  '    int BarsSinceToday(string contractNo=\'\', char kLineType=\'\', int kLineValue=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约\n' +
                                  '    kLineType K线类型\n' +
                                  '    kLineValue K线周期\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    无。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ContractProfit(contractNo=\'\')',
                insertText      : 'ContractProfit(${1})',
                detail          : '# 获得当前持仓的每手浮动盈亏。\n' +
                                  '    float ContractProfit(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓位置的每手浮动盈亏，返回值为浮点数。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CurrentContracts(contractNo=\'\')',
                insertText      : 'CurrentContracts(${1})',
                detail          : '# 获得策略当前的持仓合约数(净持仓)。\n' +
                                  '    int CurrentContracts(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得策略当前的持仓合约数，返回值为整数。\n' +
                                  '    该函数返回策略当前的净持仓数量，多仓为正值，空仓为负值，持平返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BuyPosition(contractNo=\'\')',
                insertText      : 'BuyPosition(${1})',
                detail          : '# 获得当前持仓的买入方向的持仓量。\n' +
                                  '    int BuyPosition(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得策略当前持仓的买入方向的持仓量，返回值为整数。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SellPosition(contractNo=\'\')',
                insertText      : 'SellPosition(${1})',
                detail          : '# 获得当前持仓的卖出方向的持仓量。\n' +
                                  '    int SellPosition(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得策略当前持仓的卖出持仓量，返回值为整数。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'EntryDate(contractNo=\'\')',
                insertText      : 'EntryDate(${1})',
                detail          : '# 获得当前持仓的第一个建仓位置的日期。\n' +
                                  '    int EntryDate(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若策略当前持仓为0，则返回无效日期:19700101，否则返回YYYYMMDD格式的日期。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'EntryPrice(contractNo=\'\')',
                insertText      : 'EntryPrice(${1})',
                detail          : '# 获得当前持仓的第一次建仓的委托价格。\n' +
                                  '    float EntryPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓的第一个建仓价格，返回值为浮点数。\n' +
                                  '    若策略当前持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'EntryTime(contractNo=\'\')',
                insertText      : 'EntryTime(${1})',
                detail          : '# 获得当前持仓的第一个建仓位置的时间。\n' +
                                  '    float EntryTime(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓的第一个建仓时间，返回值为0.HHMMSSmmm格式的时间。\n' +
                                  '    若策略当前持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ExitDate(contractNo=\'\')',
                insertText      : 'ExitDate(${1})',
                detail          : '# 获得最近平仓位置Bar日期。\n' +
                                  '    int ExitDate(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓的最近平仓时间，返回值为YYYYMMDD格式的日期。\n' +
                                  '    若从未平过仓，则返回无效日期:19700101。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ExitPrice(contractNo=\'\')',
                insertText      : 'ExitPrice(${1})',
                detail          : '# 获得合约最近一次平仓的委托价格。\n' +
                                  '    float ExitPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得最近平仓位置的平仓价格，返回值为浮点数。\n' +
                                  '    若合约从未被平仓,则返回0，否则返回合约最近一次平仓时的委托价格。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ExitTime(contractNo=\'\')',
                insertText      : 'ExitTime(${1})',
                detail          : '# 获得最近平仓位置Bar时间。\n' +
                                  '    float ExitTime(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得最近平仓位置Bar时间，返回值为0.HHMMSSmmm格式的时间。\n' +
                                  '    若合约从未平过仓，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LastEntryDate(contractNo=\'\')',
                insertText      : 'LastEntryDate(${1})',
                detail          : '# 获得当前持仓的最后一个建仓位置的日期。\n' +
                                  '    int LastEntryDate(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓的最后一个建仓位置的日期，返回值为YYYYMMDD格式的日期。\n' +
                                  '    若策略当前持仓为0，则返回无效日期:19700101。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LastEntryPrice(contractNo=\'\')',
                insertText      : 'LastEntryPrice(${1})',
                detail          : '# 获得当前持仓的最后一次建仓的委托价格。\n' +
                                  '    float LastEntryPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓的最后一个建仓价格，返回值为浮点数。\n' +
                                  '    若策略当前持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LastBuyEntryPrice(contractNo=\'\')',
                insertText      : 'LastBuyEntryPrice(${1})',
                detail          : '# 获得当前Buy持仓的最后一次建仓的委托价格。\n' +
                                  '    float LastBuyEntryPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前Buy持仓的最后一个建仓价格，返回值为浮点数。\n' +
                                  '    若策略当前Buy持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LastSellEntryPrice(contractNo=\'\')',
                insertText      : 'LastSellEntryPrice(${1})',
                detail          : '# 获得当前Sell持仓的最后一次建仓的委托价格。\n' +
                                  '    float LastSellEntryPrice(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前Sell持仓的最后一个建仓价格，返回值为浮点数。\n' +
                                  '    若策略当前Sell持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HighestSinceLastBuyEntry(contractNo=\'\')',
                insertText      : 'HighestSinceLastBuyEntry(${1})',
                detail          : '# 获得当前Buy持仓的最后一次建仓以来的最高价。\n' +
                                  '    float HighestSinceLastBuyEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前Buy持仓的最后一个建仓以来的最高价，返回值为浮点数。\n' +
                                  '    若策略当前Buy持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LowestSinceLastBuyEntry(contractNo=\'\')',
                insertText      : 'LowestSinceLastBuyEntry(${1})',
                detail          : '# 获得当前Buy持仓的最后一次建仓以来的最低价。\n' +
                                  '    float LowestSinceLastBuyEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前Buy持仓的最后一个建仓以来的最低价，返回值为浮点数。\n' +
                                  '    若策略当前Buy持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HighestSinceLastSellEntry(contractNo=\'\')',
                insertText      : 'HighestSinceLastSellEntry(${1})',
                detail          : '# 获得当前Sell持仓的最后一次建仓以来的最高价。\n' +
                                  '    float HighestSinceLastSellEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前Sell持仓的最后一个建仓以来的最高价，返回值为浮点数。\n' +
                                  '    若策略当前Sell持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LowestSinceLastSellEntry(contractNo=\'\')',
                insertText      : 'LowestSinceLastSellEntry(${1})',
                detail          : '# 获得当前Sell持仓的最后一次建仓以来的最低价。\n' +
                                  '    float LowestSinceLastSellEntry(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前Sell持仓的最后一个建仓以来的最低价，返回值为浮点数。\n' +
                                  '    若策略当前Sell持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LastEntryTime(contractNo=\'\')',
                insertText      : 'LastEntryTime(${1})',
                detail          : '# 获得当前持仓的最后一个建仓位置的时间。\n' +
                                  '    float LastEntryTime(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓的最后一个建仓位置的时间，返回值为0.HHMMSSmmm格式的时间。\n' +
                                  '    若策略当前持仓为0，则返回0。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MarketPosition(contractNo=\'\')',
                insertText      : 'MarketPosition(${1})',
                detail          : '# 获得当前持仓状态 。\n' +
                                  '    int MarketPosition(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获得当前持仓状态，返回值为整型。\n' +
                                  '    返回值定义如下：\n' +
                                  '    -1 当前位置为持空仓\n' +
                                  '    0 当前位置为持平\n' +
                                  '    1 当前位置为持多仓\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    if(MarketPosition(\"ZCE|F|SR|905\")==1)判断合约ZCE|F|SR|905当前是否持多仓\n' +
                                  '    if(MarketPosition(\"ZCE|F|SR|905\")!=0)判断合约ZCE|F|SR|905当前是否有持仓，无论持空仓或多仓',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PositionProfit(contractNo=\'\')',
                insertText      : 'PositionProfit(${1})',
                detail          : '# 获得当前持仓的浮动盈亏 。\n' +
                                  '    float PositionProfit(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，默认为基准合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若策略当前持仓为0，则返回0',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BarsLast(bool condition)',
                insertText      : 'BarsLast(${1})',
                detail          : '# 返回最后一次满足条件时距离当前的bar数\n' +
                                  '    int BarsLast(bool condition)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    condition  传入的条件表达式\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回最后一次满足条件时距离当前的bar数。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    BarsLast(Close >Open); 从当前Bar开始，最近出现Close>Open的Bar到当前Bar的偏移值。如果为0，即当前Bar为最近的满足条件的Bar。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Available()',
                insertText      : 'Available()',
                detail          : '# 返回策略当前可用虚拟资金。\n' +
                                  '    float Available()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'CurrentEquity()',
                insertText      : 'CurrentEquity()',
                detail          : '# 返回策略的当前账户权益。\n' +
                                  '    float CurrentEquity()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'FloatProfit(contractNo=\'\')',
                insertText      : 'FloatProfit(${1})',
                detail          : '# 返回指定合约的浮动盈亏。\n' +
                                  '    float FloatProfit(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时返回基准合约的浮动盈亏。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'GrossLoss()',
                insertText      : 'GrossLoss()',
                detail          : '# 返回累计总亏损。\n' +
                                  '    float GrossLoss()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'GrossProfit()',
                insertText      : 'GrossProfit()',
                detail          : '# 返回累计总利润。\n' +
                                  '    float GrossProfit()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'Margin(contractNo=\'\')',
                insertText      : 'Margin(${1})',
                detail          : '# 返回指定合约的持仓保证金。\n' +
                                  '    float Margin(string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空时返回基准合约的浮动盈亏。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'NetProfit()',
                insertText      : 'NetProfit()',
                detail          : '# 返回该账户下的平仓盈亏。\n' +
                                  '    float NetProfit()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'NumEvenTrades()',
                insertText      : 'NumEvenTrades()',
                detail          : '# 返回该账户下保本交易的总手数。\n' +
                                  '    int NumEvenTrades()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'NumLosTrades()',
                insertText      : 'NumLosTrades()',
                detail          : '# 返回该账户下亏损交易的总手数。\n' +
                                  '    int NumLosTrades()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'NumWinTrades()',
                insertText      : 'NumWinTrades()',
                detail          : '# 返回该账户下盈利交易的总手数。\n' +
                                  '    int NumWinTrades()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'NumAllTimes()',
                insertText      : 'NumAllTimes()',
                detail          : '# 返回该账户的开仓次数。\n' +
                                  '    int NumAllTimes()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'NumWinTimes()',
                insertText      : 'NumWinTimes()',
                detail          : '# 返回该账户的盈利次数。\n' +
                                  '    int NumWinTimes()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'NumLoseTimes()',
                insertText      : 'NumLoseTimes()',
                detail          : '# 返回该账户的亏损次数。\n' +
                                  '    int NumLoseTimes()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'NumEventTimes()',
                insertText      : 'NumEventTimes()',
                detail          : '# 返回该账户的保本次数。\n' +
                                  '    int NumEventTimes()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'PercentProfit()',
                insertText      : 'PercentProfit()',
                detail          : '# 返回该账户的盈利成功率。\n' +
                                  '    float PercentProfit()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'TradeCost()',
                insertText      : 'TradeCost()',
                detail          : '# 返回该账户交易产生的手续费。\n' +
                                  '    float TradeCost()',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'TotalTrades()',
                insertText      : 'TotalTrades(${1})',
                detail          : '# 返回该账户的交易总开仓手数。\n' +
                                  '    int TotalTrades()',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_AccountID()',
                insertText      : 'A_AccountID()',
                detail          : '# 返回当前公式应用的交易帐户ID。\n' +
                                  '    string A_AccountID()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回当前公式应用的交易帐户ID，返回值为字符串，无效时返回空串。\n' +
                                  '    注：不能用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'A_AllAccountID()',
                insertText      : 'A_AllAccountID()',
                detail          : '# 返回所有已登录交易帐户ID。\n' +
                                  '    list A_AllAccountID()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    没有账号登录时，返回空列表\n' +
                                  '    注：不能用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'A_GetAllPositionSymbol(userNo=\'\')',
                insertText      : 'A_GetAllPositionSymbol(${1})',
                detail          : '# 获得指定账户所有持仓合约。\n' +
                                  '    list A_GetAllPositionSymbol(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该参数返回类型为字符串列表，列表内容为账户所有持仓合约列表。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_Cost(userNo=\'\')',
                insertText      : 'A_Cost(${1})',
                detail          : '# 返回指定交易帐户的手续费。\n' +
                                  '    string A_Cost(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定交易帐户的手续费，返回值为浮点数。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_Assets(userNo=\'\')',
                insertText      : 'A_Assets(${1})',
                detail          : '# 返回指定交易帐户的动态权益。\n' +
                                  '    float A_Assets(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定交易帐户的动态权益，返回值为浮点数。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_Available(userNo=\'\')',
                insertText      : 'A_Available(${1})',
                detail          : '# 返回指定交易帐户的可用资金。\n' +
                                  '    float A_Available(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定交易帐户的可用资金，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_Margin(userNo=\'\')',
                insertText      : 'A_Margin(${1})',
                detail          : '# 返回指定交易帐户的持仓保证金。\n' +
                                  '    float A_Margin(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定交易帐户的持仓保证金，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_ProfitLoss(userNo=\'\')',
                insertText      : 'A_ProfitLoss(${1})',
                detail          : '# 返回指定交易帐户的浮动盈亏。\n' +
                                  '    float A_ProfitLoss(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定交易帐户的浮动盈亏，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_CoverProfit(userNo=\'\')',
                insertText      : 'A_CoverProfit(${1})',
                detail          : '# 返回当前账户的平仓盈亏。\n' +
                                  '    float A_CoverProfit(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定交易帐户的平仓盈亏，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_TotalFreeze(userNo=\'\')',
                insertText      : 'A_TotalFreeze(${1})',
                detail          : '# 返回指定交易帐户的冻结资金。\n' +
                                  '    float A_TotalFreeze(string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定交易帐户的冻结资金，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_BuyAvgPrice(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_BuyAvgPrice(${1})',
                detail          : '# 返回指定帐户下当前商品的买入持仓均价。\n' +
                                  '    float A_BuyAvgPrice(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的买入持仓均价，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_BuyPosition(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_BuyPosition(${1})',
                detail          : '# 返回指定帐户下当前商品的买入持仓。\n' +
                                  '    float A_BuyPosition(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的买入持仓，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    当前持多仓2手，A_BuyPosition返回2。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_BuyPositionCanCover(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_BuyPositionCanCover(${1})',
                detail          : '# 返回指定帐户下买仓可平数量。\n' +
                                  '    int A_BuyPositionCanCover(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    可平仓数量=持仓数量-已排队的挂单数量',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_BuyProfitLoss(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_BuyProfitLoss(${1})',
                detail          : '# 返回指定帐户下当前商品的买入持仓盈亏。\n' +
                                  '    float A_BuyProfitLoss(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的买入持仓盈亏，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_SellAvgPrice(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_SellAvgPrice(${1})',
                detail          : '# 返回指定帐户下当前商品的卖出持仓均价。\n' +
                                  '    float A_SellAvgPrice(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的卖出持仓均价，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_SellPosition(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_SellPosition(${1})',
                detail          : '# 返回指定帐户下当前商品的卖出持仓。\n' +
                                  '    float A_SellPosition(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的卖出持仓，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    当前持空仓3手，A_SellPosition返回3。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_SellPositionCanCover(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_SellPositionCanCover(${1})',
                detail          : '# 返回指定帐户下卖仓可平数量。\n' +
                                  '    int A_SellPositionCanCover(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    可平仓数量=持仓数量-已排队的挂单数量',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_SellProfitLoss(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_SellProfitLoss(${1})',
                detail          : '# 返回指定帐户下当前商品的卖出持仓盈亏。\n' +
                                  '    float A_SellProfitLoss(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的卖出持仓盈亏，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_TotalAvgPrice(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_TotalAvgPrice(${1})',
                detail          : '# 返回指定帐户下当前商品的持仓均价。\n' +
                                  '    float A_TotalAvgPrice(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的持仓均价，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_TotalPosition(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_TotalPosition(${1})',
                detail          : '# 返回指定帐户下当前商品的总持仓。\n' +
                                  '    int A_TotalPosition(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的总持仓，返回值为浮点数。\n' +
                                  '    该持仓为所有持仓的合计值，正数表示多仓，负数表示空仓，零为无持仓。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_TotalProfitLoss(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_TotalProfitLoss(${1})',
                detail          : '# 返回指定帐户下当前商品的总持仓盈亏。\n' +
                                  '    float A_TotalProfitLoss(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的总持仓盈亏，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_TodayBuyPosition(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_TodayBuyPosition(${1})',
                detail          : '# 返回指定帐户下当前商品的当日买入持仓。\n' +
                                  '    float A_TodayBuyPosition(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的当日买入持仓，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_TodaySellPosition(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_TodaySellPosition(${1})',
                detail          : '# 返回指定帐户下当前商品的当日卖出持仓。\n' +
                                  '    float A_TodaySellPosition(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo，指定商品的合约编号，为空时采用基准合约编号。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的当日卖出持仓，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderBuyOrSell(localOrderId=\'\')',
                insertText      : 'A_OrderBuyOrSell(${1})',
                detail          : '# 返回指定帐户下当前商品的某个委托单的买卖类型。\n' +
                                  '    char A_OrderBuyOrSell(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的买卖类型，返回值为：\n' +
                                  '    B : 买入\n' +
                                  '    S : 卖出\n' +
                                  '    A : 双边\n' +
                                  '    该函数返回值可以与Enum_Buy、Enum_Sell等买卖状态枚举值进行比较，根据类型不同分别处理。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    nBorS = A_OrderBuyOrSell(\'1-1\')\n' +
                                  '    if nBorS == Enum_Buy():\n' +
                                  '    ...',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderEntryOrExit(localOrderId=\'\')',
                insertText      : 'A_OrderEntryOrExit(${1})',
                detail          : '# 返回指定帐户下当前商品的某个委托单的开平仓状态。\n' +
                                  '    char A_OrderEntryOrExit(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的开平仓状态，返回值：\n' +
                                  '    N : 无\n' +
                                  '    O : 开仓\n' +
                                  '    C : 平仓\n' +
                                  '    T : 平今\n' +
                                  '    1 : 开平，应价时有效, 本地套利也可以\n' +
                                  '    2 : 平开，应价时有效, 本地套利也可以\n' +
                                  '    该函数返回值可以与Enum_Entry、Enum_Exit等开平仓状态枚举值进行比较，根据类型不同分别处理。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    orderFlag = A_OrderEntryOrExit(\'1-1\')\n' +
                                  '    if orderFlag == Enum_Exit():\n' +
                                  '    ...',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderFilledLot(localOrderId=\'\')',
                insertText      : 'A_OrderFilledLot(${1})',
                detail          : '# 返回指定帐户下当前商品的某个委托单的成交数量。\n' +
                                  '    float A_OrderFilledLot(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的成交数量，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderFilledPrice(localOrderId=\'\')',
                insertText      : 'A_OrderFilledPrice(${1})',
                detail          : '# 返回指定帐户下当前商品的某个委托单的成交价格。\n' +
                                  '    float A_OrderFilledPrice(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的成交价格，返回值为浮点数。\n' +
                                  '    该成交价格可能为多个成交价格的平均值。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderLot(localOrderId=\'\')',
                insertText      : 'A_OrderLot(${1})',
                detail          : '# 返回指定帐户下当前商品的某个委托单的委托数量。\n' +
                                  '    float A_OrderLot(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的委托数量，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderPrice(localOrderId=\'\')',
                insertText      : 'A_OrderPrice(${1})',
                detail          : '# 返回指定帐户下当前商品的某个委托单的委托价格。\n' +
                                  '    float A_OrderPrice(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的委托价格，返回值为浮点数。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderStatus(localOrderId=\'\')',
                insertText      : 'A_OrderStatus(${1})',
                detail          : '# 返回指定帐户下当前商品的某个委托单的状态。\n' +
                                  '    char A_OrderStatus(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的状态，返回值：\n' +
                                  '    N : 无\n' +
                                  '    0 : 已发送\n' +
                                  '    1 : 已受理\n' +
                                  '    2 : 待触发\n' +
                                  '    3 : 已生效\n' +
                                  '    4 : 已排队\n' +
                                  '    5 : 部分成交\n' +
                                  '    6 : 完全成交\n' +
                                  '    7 : 待撤\n' +
                                  '    8 : 待改\n' +
                                  '    9 : 已撤单\n' +
                                  '    A : 已撤余单\n' +
                                  '    B : 指令失败\n' +
                                  '    C : 待审核\n' +
                                  '    D : 已挂起\n' +
                                  '    E : 已申请\n' +
                                  '    F : 无效单\n' +
                                  '    G : 部分触发\n' +
                                  '    H : 完全触发\n' +
                                  '    I : 余单失败\n' +
                                  '    该函数返回值可以与委托状态枚举函数Enum_Sended、Enum_Accept等函数进行比较，根据类型不同分别处理。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderIsClose(localOrderId=\'\')',
                insertText      : 'A_OrderIsClose(${1})',
                detail          : '# 判断某个委托单是否完结。\n' +
                                  '    bool A_OrderIsClose(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    当委托单是完结状态，返回True，否则返回False。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderTime(localOrderId=\'\')',
                insertText      : 'A_OrderTime(${1})',
                detail          : '# 返回指定公式应用的帐户下当前商品的某个委托单的委托时间。\n' +
                                  '    struct_time A_OrderTime(int|string localOrderId=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回指定帐户下当前商品的某个委托单的委托时间，返回格式为YYYYMMDD.hhmmss的数值。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_FirstOrderNo(contractNo1=\'\', contractNo2=\'\', userNo=\'\')',
                insertText      : 'A_FirstOrderNo(${1})',
                detail          : '# 返回指定账户第一个订单号。\n' +
                                  '    int A_FirstOrderNo(string contractNo1=\'\', string contractNo2=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo1 合约代码，默认为遍历所有合约。\n' +
                                  '    contractNo2 合约代码，默认为遍历所有合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若返回值为-1，表示没有任何订单，否则，返回第一个订单的索引值，\n' +
                                  '    该函数经常和A_NextOrderNo函数合用，用于遍历所有的订单。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_NextOrderNo(localOrderId=0, contractNo1=\'\', contractNo2=\'\', userNo=\'\')',
                insertText      : 'A_NextOrderNo(${1})',
                detail          : '# 返回指定账户下一个订单号。\n' +
                                  '    int A_NextOrderNo(int localOrderId=0, string contractNo1=\'\', string contractNo2=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，默认为0，\n' +
                                  '    contractNo1 合约代码，默认为遍历所有合约。\n' +
                                  '    contractNo2 合约代码，默认为遍历所有合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若返回值为-1，表示没有任何订单，否则，返回处在OrderNo后面的订单索引值，\n' +
                                  '    该函数常和A_FirstOrderNo联合使用。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_LastOrderNo(contractNo1=\'\', contractNo2=\'\', userNo=\'\')',
                insertText      : 'A_LastOrderNo(${1})',
                detail          : '# 返回指定账户最近发送的订单号。\n' +
                                  '    int A_LastOrderNo(string contractNo1=\'\', string contractNo2=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo1 合约代码，默认为遍历所有合约。\n' +
                                  '    contractNo2 合约代码，默认为遍历所有合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若返回值为-1，表示没有任何订单，否则，返回最后一个订单的索引值。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_FirstQueueOrderNo(contractNo1=\'\', contractNo2=\'\', userNo=\'\')',
                insertText      : 'A_FirstQueueOrderNo(${1})',
                detail          : '# 返回指定账户第一个排队(可撤)订单号。\n' +
                                  '    int A_FirstQueueOrderNo(string contractNo1=\'\', string contractNo2=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo1 合约代码，默认为遍历所有合约。\n' +
                                  '    contractNo2 合约代码，默认为遍历所有合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若返回值为-1，表示没有任何可撤排队订单，否则，返回第一个订单的索引值。，\n' +
                                  '    该函数经常和A_NextQueueOrderNo函数合用，用于遍历排队中的订单。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_NextQueueOrderNo(localOrderId=0, contractNo1=\'\', contractNo2=\'\', userNo=\'\')',
                insertText      : 'A_NextQueueOrderNo(${1})',
                detail          : '# 返回指定账户下一个排队(可撤)订单号。\n' +
                                  '    int A_NextQueueOrderNo(int localOrderId=0, string contractNo1=\'\', string contractNo2=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，默认为0，\n' +
                                  '    contractNo1 合约代码，默认为遍历所有合约。\n' +
                                  '    contractNo2 合约代码，默认为遍历所有合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若返回值为-1，表示没有任何排队订单，否则，返回处在OrderNo后面的订单索引值，\n' +
                                  '    该函数常和A_FirstQueueOrderNo联合使用。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_AllQueueOrderNo(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_AllQueueOrderNo(${1})',
                detail          : '# 返回指定账户所有排队(可撤)订单号。\n' +
                                  '    list A_AllQueueOrderNo(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约代码，默认为遍历所有合约，指定后只遍历指定合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若返回值为空列表，表示没有任何排队订单，否则，返回包含处于排队中的委托定单号的列表。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_LatestFilledTime(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_LatestFilledTime(${1})',
                detail          : '# 返回指定账户最新一笔完全成交委托单对应的时间。\n' +
                                  '    float A_LatestFilledTime(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约代码，默认为遍历所有合约，指定后只遍历指定合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    若返回值为-1，表示没有对应的完全成交的委托，否则，返回最新一笔完全成交委托单对应的时间，返回格式为YYYYMMDD.hhmmss的数值。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_AllOrderNo(contractNo=\'\', userNo=\'\')',
                insertText      : 'A_AllOrderNo(${1})',
                detail          : '# 返回包含指定合约指定账户所有订单号的列表。\n' +
                                  '    list A_AllOrderNo(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约代码，默认为遍历所有合约，指定后只遍历指定合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_OrderContractNo(localOrderId=0)',
                insertText      : 'A_OrderContractNo(${1})',
                detail          : '# 返回订单的合约号。\n' +
                                  '    string A_OrderContractNo(int|string localOrderId=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回结果如：\"ZCE|F|TA|305\"等，\n' +
                                  '    如果localOrderId没有对应的委托单，则返回结果为字符串。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_SendOrder(orderDirct, entryOrExit, orderQty, orderPrice, contractNo=\'\', userNo=\'\', orderType=\'2\', validType=\'0\', hedge=\'T\', triggerType=\'N\', triggerMode=\'N\', triggerCondition=\'N\', triggerPrice=0)',
                insertText      : 'A_SendOrder(${1})',
                detail          : '# 针对指定的帐户、商品发送委托单。\n' +
                                  '    int. string A_SendOrder(char orderDirct, char entryOrExit, int orderQty, float orderPrice, string contractNo=\'\', string userNo=\'\', char orderType=\'2\', char validType=\'0\', char hedge=\'T\', char triggerType=\'N\', char triggerMode=\'N\', char triggerCondition=\'N\', float triggerPrice=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    orderDirct 发送委托单的买卖类型，取值为Enum_Buy或Enum_Sell之一，\n' +
                                  '    entryOrExit 发送委托单的开平仓类型，取值为Enum_Entry,Enum_Exit,Enum_ExitToday之一，\n' +
                                  '    orderQty 委托单的交易数量，\n' +
                                  '    orderPrice 委托单的交易价格，\n' +
                                  '    contractNo 商品合约编号，默认值为基准合约，\n' +
                                  '    userNo 指定的账户名称，默认为界面选定的账户名称，\n' +
                                  '    orderType 订单类型，字符类型，默认值为\'2\'，可选值为：\n' +
                                  '    \'1\' : 市价单\n' +
                                  '    \'2\' : 限价单\n' +
                                  '    \'3\' : 市价止损\n' +
                                  '    \'4\' : 限价止损\n' +
                                  '    \'5\' : 行权\n' +
                                  '    \'6\' : 弃权\n' +
                                  '    \'7\' : 询价\n' +
                                  '    \'8\' : 应价\n' +
                                  '    \'9\' : 冰山单\n' +
                                  '    \'A\' : 影子单\n' +
                                  '    \'B\' : 互换\n' +
                                  '    \'C\' : 套利申请\n' +
                                  '    \'D\' : 套保申请\n' +
                                  '    \'F\' : 行权前期权自对冲申请\n' +
                                  '    \'G\' : 履约期货自对冲申请\n' +
                                  '    \'H\' : 做市商留仓\n' +
                                  '    可使用如Enum_Order_Market、Enum_Order_Limit等订单类型枚举函数获取相应的类型，\n' +
                                  '    validType 订单有效类型，字符类型，默认值为\'0\'， 可选值为：\n' +
                                  '    \'0\' : 当日有效\n' +
                                  '    \'1\' : 长期有效\n' +
                                  '    \'2\' : 限期有效\n' +
                                  '    \'3\' : 即时部分\n' +
                                  '    \'4\' : 即时全部\n' +
                                  '    可使用如Enum_GFD、Enum_GTC等订单有效类型枚举函数获取相应的类型，\n' +
                                  '    hedge 投保标记，字符类型，默认值为\'T\'，可选值为：\n' +
                                  '    \'T\' : 投机\n' +
                                  '    \'B\' : 套保\n' +
                                  '    \'S\' : 套利\n' +
                                  '    \'M\' : 做市\n' +
                                  '    可使用如Enum_Speculate、Enum_Hedge等订单投保标记枚举函数获取相应的类型，\n' +
                                  '    triggerType 触发委托类型，默认值为\'N\'，可用的值为：\n' +
                                  '    \'N\' : 普通单\n' +
                                  '    \'P\' : 预备单(埋单)\n' +
                                  '    \'A\' : 自动单\n' +
                                  '    \'C\' : 条件单\n' +
                                  '    triggerMode 触发模式，默认值为\'N\'，可用的值为：\n' +
                                  '    \'N\' : 普通单\n' +
                                  '    \'L\' : 最新价\n' +
                                  '    \'B\' : 买价\n' +
                                  '    \'A\' : 卖价\n' +
                                  '    triggerCondition 触发条件，默认值为\'N\'，可用的值为：\n' +
                                  '    \'N\' : 无\n' +
                                  '    \'g\' : 大于\n' +
                                  '    \'G\' : 大于等于\n' +
                                  '    \'l\' : 小于\n' +
                                  '    \'L\' : 小于等于\n' +
                                  '    triggerPrice 触发价格，默认价格为0。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    针对当前公式指定的帐户、商品发送委托单，发送成功返回如\"1-2\"的下单编号，发送失败返回空字符串\"\"。\n' +
                                  '    返回结果形式未：retCode, retMsg，retCode的数据类型为可以为负的整数, retMsg的数据类型为字符串。\n' +
                                  '    其中发送成功时retCode为0，retMsg为返回的下单编号localOrderId，其组成规则为：策略id-该策略中发送委托单的次数，所以下单编号\"1-2\"表示在策略id为1的策略中的第2次发送委托单返回的下单编号。\n' +
                                  '    当发送失败时retCode为负数，retMsg为返回的发送失败的原因，retCode可能返回的值及含义如下：\n' +
                                  '    -1 : 未选择实盘运行，请在设置界面勾选\"实盘运行\"，或者在策略代码中调用SetActual()方法选择实盘运行；\n' +
                                  '    -2 : 策略当前状态不是实盘运行状态，请勿在历史回测阶段调用该函数；\n' +
                                  '    -3 : 未指定下单账户信息；\n' +
                                  '    -4 : 输入的账户没有在极星客户端登录；\n' +
                                  '    -5 : 请调用StartTrade方法开启实盘下单功能。\n' +
                                  '    该函数直接发单，不经过任何确认，并会在每次公式计算时发送，一般需要配合着仓位头寸进行条件处理，在不清楚运行机制的情况下，请慎用。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    retCode, retMsg = A_SendOrder(Enum_Buy(), Enum_Exit(), 1, Q_AskPrice())\n' +
                                  '    当retCode为0时表明发送订单信息成功，retMsg为返回的下单编号localOrderId。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_ModifyOrder(localOrderId, orderDirct, entryOrExit, orderQty, orderPrice, contractNo=\'\', userNo=\'\', orderType=\'2\', validType=\'0\', hedge=\'T\', triggerType=\'N\', triggerMode=\'N\', triggerCondition=\'N\', triggerPrice=0)',
                insertText      : 'A_ModifyOrder(${1})',
                detail          : '# 发送改单指令。\n' +
                                  '    bool A_ModifyOrder(string localOrderId, char orderDirct, char entryOrExit, int orderQty, float orderPrice, string contractNo=\'\', string userNo=\'\', char orderType=\'2\', char validType=\'0\', char hedge=\'T\', char triggerType=\'N\', char triggerMode=\'N\', char triggerCondition=\'N\', float triggerPrice=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号，\n' +
                                  '    orderDirct 发送委托单的买卖类型，取值为Enum_Buy或Enum_Sell之一，\n' +
                                  '    entryOrExit 发送委托单的开平仓类型，取值为Enum_Entry,Enum_Exit,Enum_ExitToday之一，\n' +
                                  '    orderQty 委托单的交易数量，\n' +
                                  '    orderPrice 委托单的交易价格，\n' +
                                  '    contractNo 商品合约编号，默认值为基准合约，\n' +
                                  '    userNo 指定的账户名称，默认为界面选定的账户名称，\n' +
                                  '    orderType 订单类型，字符类型，默认值为\'2\'，可选值为：\n' +
                                  '    \'1\' : 市价单\n' +
                                  '    \'2\' : 限价单\n' +
                                  '    \'3\' : 市价止损\n' +
                                  '    \'4\' : 限价止损\n' +
                                  '    \'5\' : 行权\n' +
                                  '    \'6\' : 弃权\n' +
                                  '    \'7\' : 询价\n' +
                                  '    \'8\' : 应价\n' +
                                  '    \'9\' : 冰山单\n' +
                                  '    \'A\' : 影子单\n' +
                                  '    \'B\' : 互换\n' +
                                  '    \'C\' : 套利申请\n' +
                                  '    \'D\' : 套保申请\n' +
                                  '    \'F\' : 行权前期权自对冲申请\n' +
                                  '    \'G\' : 履约期货自对冲申请\n' +
                                  '    \'H\' : 做市商留仓\n' +
                                  '    可使用如Enum_Order_Market、Enum_Order_Limit等订单类型枚举函数获取相应的类型，\n' +
                                  '    validType 订单有效类型，字符类型，默认值为\'0\'， 可选值为：\n' +
                                  '    \'0\' : 当日有效\n' +
                                  '    \'1\' : 长期有效\n' +
                                  '    \'2\' : 限期有效\n' +
                                  '    \'3\' : 即时部分\n' +
                                  '    \'4\' : 即时全部\n' +
                                  '    可使用如Enum_GFD、Enum_GTC等订单有效类型枚举函数获取相应的类型，\n' +
                                  '    hedge 投保标记，字符类型，默认值为\'T\'，可选值为：\n' +
                                  '    \'T\' : 投机\n' +
                                  '    \'B\' : 套保\n' +
                                  '    \'S\' : 套利\n' +
                                  '    \'M\' : 做市\n' +
                                  '    可使用如Enum_Speculate、Enum_Hedge等订单投保标记枚举函数获取相应的类型，\n' +
                                  '    triggerType 触发委托类型，默认值为\'N\'，可用的值为：\n' +
                                  '    \'N\' : 普通单\n' +
                                  '    \'P\' : 预备单(埋单)\n' +
                                  '    \'A\' : 自动单\n' +
                                  '    \'C\' : 条件单\n' +
                                  '    triggerMode 触发模式，默认值为\'N\'，可用的值为：\n' +
                                  '    \'N\' : 普通单\n' +
                                  '    \'L\' : 最新价\n' +
                                  '    \'B\' : 买价\n' +
                                  '    \'A\' : 卖价\n' +
                                  '    triggerCondition 触发条件，默认值为\'N\'，可用的值为：\n' +
                                  '    \'N\' : 无\n' +
                                  '    \'g\' : 大于\n' +
                                  '    \'G\' : 大于等于\n' +
                                  '    \'l\' : 小于\n' +
                                  '    \'L\' : 小于等于\n' +
                                  '    triggerPrice 触发价格，默认价格为0。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    针对指定帐户、订单发送改单指令，发送成功返回True, 发送失败返回False。\n' +
                                  '    该函数直接发单，不经过任何确认，并会在每次公式计算时发送，一般需要配合着仓位头寸进行条件处理，在不清楚运行机制的情况下，请慎用。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_DeleteOrder(localOrderId)',
                insertText      : 'A_DeleteOrder(${1})',
                detail          : '# 针对指定帐户、商品发送撤单指令。\n' +
                                  '    bool A_DeleteOrder(int|string localOrderId)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 定单号，或者使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    针对指定帐户、商品发送撤单指令，发送成功返回True, 发送失败返回False。\n' +
                                  '    该函数直接发单，不经过任何确认，并会在每次公式计算时发送，一般需要配合着仓位头寸进行条件处理，在不清楚运行机制的情况下，请慎用。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'A_GetOrderNo(localOrderId)',
                insertText      : 'A_GetOrderNo(${1})',
                detail          : '# 获取下单编号对应的定单号和委托号。\n' +
                                  '    string, string A_GetOrderNo(string localOrderId)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    localOrderId 使用A_SendOrder返回的下单编号。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    针对当前策略使用A_SendOrder返回的下单编号，可以使用A_GetOrderNo获取下单编号对应的定单号和委托号。\n' +
                                  '    由于使用A_SendOrder返回的下单编号localOrderId与策略相关，所以在策略重启后localOrderId会发生变化。\n' +
                                  '    由于委托单对应的定单号与客户端有关，所以在客户端重启后，委托单对应的定单号可能会发生变化。\n' +
                                  '    由于委托号是服务器生成的，所以在使用A_SendOrder得到下单编号后，如果服务器还没有返回相应的委托单信息，可能获取不到相应的定单号和委托号。\n' +
                                  '    当localOrderId对应的定单号和委托号还没有从服务器返回，则对应的值为空字符串。\n' +
                                  '    注：不能使用于历史测试，仅适用于实时行情交易。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    retCode, retMsg = A_SendOrder(.....)\n' +
                                  '    time.sleep(5)\n' +
                                  '    if retCode == 0:\n' +
                                  '    sessionId, orderNo =  A_GetOrderNo(retMsg)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'DeleteAllOrders(contractNo=\'\', userNo=\'\')',
                insertText      : 'DeleteAllOrders(${1})',
                detail          : '# 批量撤单函数。\n' +
                                  '    bool DeleteAllOrders(string contractNo=\'\', string userNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约代码，默认为所有合约，指定后只撤指定合约。\n' +
                                  '    userNo  指定的交易账户，默认当前账户\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    本函数将检查指定账户下所有处于排队状态的订单，并依次发送撤单指令',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Enum_Buy()',
                insertText      : 'Enum_Buy()',
                detail          : '# 返回买卖状态的买入枚举值\n' +
                                  '    char Enum_Buy()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Sell()',
                insertText      : 'Enum_Sell()',
                detail          : '# 返回买卖状态的卖出枚举值\n' +
                                  '    char Enum_Sell()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Entry()',
                insertText      : 'Enum_Entry()',
                detail          : '# 返回开平状态的开仓枚举值\n' +
                                  '    char Enum_Entry()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Exit()',
                insertText      : 'Enum_Exit()',
                detail          : '# 返回开平状态的平仓枚举值\n' +
                                  '    char Enum_Exit()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_ExitToday()',
                insertText      : 'Enum_ExitToday()',
                detail          : '# 返回开平状态的平今枚举值\n' +
                                  '    char Enum_ExitToday()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_EntryExitIgnore()',
                insertText      : 'Enum_EntryExitIgnore()',
                detail          : '# 返回开平状态不区分开平的枚举值\n' +
                                  '    char Enum_EntryExitIgnore()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Sended()',
                insertText      : 'Enum_Sended()',
                detail          : '# 返回委托状态为已发送的枚举值\n' +
                                  '    char Enum_Sended()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Accept()',
                insertText      : 'Enum_Accept()',
                detail          : '# 返回委托状态为已受理的枚举值\n' +
                                  '    char Enum_Accept()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Triggering()',
                insertText      : 'Enum_Triggering()',
                detail          : '# 返回委托状态为待触发的枚举值\n' +
                                  '    char Enum_Triggering()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Active()',
                insertText      : 'Enum_Active()',
                detail          : '# 返回委托状态为已生效的枚举值\n' +
                                  '    char Enum_Active()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Queued()',
                insertText      : 'Enum_Queued()',
                detail          : '# 返回委托状态为已排队的枚举值\n' +
                                  '    char Enum_Queued()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_FillPart()',
                insertText      : 'Enum_FillPart()',
                detail          : '# 返回委托状态为部分成交的枚举值\n' +
                                  '    char Enum_FillPart()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Filled()',
                insertText      : 'Enum_Filled()',
                detail          : '# 返回委托状态为全部成交的枚举值\n' +
                                  '    char Enum_Filled()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Canceling()',
                insertText      : 'Enum_Canceling()',
                detail          : '# 返回委托状态为待撤的枚举值\n' +
                                  '    char Enum_Canceling()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Modifying()',
                insertText      : 'Enum_Modifying()',
                detail          : '# 返回委托状态为待改的枚举值\n' +
                                  '    char Enum_Modifying()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Canceled()',
                insertText      : 'Enum_Canceled()',
                detail          : '# 返回委托状态为已撤单的枚举值\n' +
                                  '    char Enum_Canceled()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_PartCanceled()',
                insertText      : 'Enum_PartCanceled()',
                detail          : '# 返回委托状态为已撤余单的枚举值\n' +
                                  '    char Enum_PartCanceled()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Fail()',
                insertText      : 'Enum_Fail()',
                detail          : '# 返回委托状态为指令失败的枚举值\n' +
                                  '    char Enum_Fail()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Suspended()',
                insertText      : 'Enum_Suspended()',
                detail          : '# 返回委托状态为已挂起的枚举值\n' +
                                  '    char Enum_Suspended()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Apply()',
                insertText      : 'Enum_Apply()',
                detail          : '# 返回委托状态为已申请的枚举值\n' +
                                  '    char Enum_Apply()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Tick()',
                insertText      : 'Enum_Period_Tick()',
                detail          : '# 返回周期类型成交明细的枚举值\n' +
                                  '    char Enum_Period_Tick()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'Enum_Period_Dyna()',
                insertText      : 'Enum_Period_Dyna()',
                detail          : '# 返回周期类型分时图枚举值\n' +
                                  '    char Enum_Period_Dyna()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Second()',
                insertText      : 'Enum_Period_Second()',
                detail          : '# 返回周期类型秒线的枚举值\n' +
                                  '    char Enum_Period_Second()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Min()',
                insertText      : 'Enum_Period_Min()',
                detail          : '# 返回周期类型分钟线的枚举值\n' +
                                  '    char Enum_Period_Min()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Hour()',
                insertText      : 'Enum_Period_Hour()',
                detail          : '# 返回周期类型小时线的枚举值\n' +
                                  '    char Enum_Period_Hour()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Day()',
                insertText      : 'Enum_Period_Day()',
                detail          : '# 返回周期类型日线的枚举值\n' +
                                  '    char Enum_Period_Day()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Week()',
                insertText      : 'Enum_Period_Week()',
                detail          : '# 返回周期类型周线的枚举值\n' +
                                  '    char Enum_Period_Week()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Month()',
                insertText      : 'Enum_Period_Month()',
                detail          : '# 返回周期类型月线的枚举值\n' +
                                  '    char Enum_Period_Month()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_Year()',
                insertText      : 'Enum_Period_Year()',
                detail          : '# 返回周期类型年线的枚举值\n' +
                                  '    char Enum_Period_Year()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Period_DayX()',
                insertText      : 'Enum_Period_DayX()',
                detail          : '# 返回周期类型多日线的枚举值\n' +
                                  '    char Enum_Period_DayX()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'RGB_Red()',
                insertText      : 'RGB_Red()',
                detail          : '# 返回颜色类型红色的枚举值\n' +
                                  '    int RGB_Red()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回16进制颜色代码',
                kind            : monaco.languages.CompletionItemKind.Color
            },{
                label           : 'RGB_Green()',
                insertText      : 'RGB_Green()',
                detail          : '# 返回颜色类型绿色的枚举值\n' +
                                  '    int RGB_Green()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回16进制颜色代码',
                kind            : monaco.languages.CompletionItemKind.Color
            },{
                label           : 'RGB_Blue()',
                insertText      : 'RGB_Blue()',
                detail          : '# 返回颜色类型蓝色的枚举值\n' +
                                  '    int RGB_Blue()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回16进制颜色代码',
                kind            : monaco.languages.CompletionItemKind.Color
            },{
                label           : 'RGB_Yellow()',
                insertText      : 'RGB_Yellow()',
                detail          : '# 返回颜色类型黄色的枚举值\n' +
                                  '    int RGB_Yellow()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回16进制颜色代码',
                kind            : monaco.languages.CompletionItemKind.Color
            },{
                label           : 'RGB_Purple()',
                insertText      : 'RGB_Purple()',
                detail          : '# 返回颜色类型紫色的枚举值\n' +
                                  '    int RGB_Purple()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回16进制颜色代码',
                kind            : monaco.languages.CompletionItemKind.Color
            },{
                label           : 'RGB_Gray()',
                insertText      : 'RGB_Gray()',
                detail          : '# 返回颜色类型灰色的枚举值\n' +
                                  '    int RGB_Gray()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回16进制颜色代码',
                kind            : monaco.languages.CompletionItemKind.Color
            },{
                label           : 'RGB_Brown()',
                insertText      : 'RGB_Brown()',
                detail          : '# 返回颜色类型褐色的枚举值\n' +
                                  '    int RGB_Brown()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回16进制颜色代码',
                kind            : monaco.languages.CompletionItemKind.Color
            },{
                label           : 'Enum_Order_Market()',
                insertText      : 'Enum_Order_Market()',
                detail          : '# 返回订单类型市价单的枚举值\n' +
                                  '    char Enum_Order_Market()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Limit()',
                insertText      : 'Enum_Order_Limit()',
                detail          : '# 返回订单类型限价单的枚举值\n' +
                                  '    char Enum_Order_Limit()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_MarketStop()',
                insertText      : 'Enum_Order_MarketStop()',
                detail          : '# 返回订单类型市价止损单的枚举值\n' +
                                  '    char Enum_Order_MarketStop()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_LimitStop()',
                insertText      : 'Enum_Order_LimitStop()',
                detail          : '# 返回订单类型限价止损单的枚举值\n' +
                                  '    char Enum_Order_LimitStop()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Execute()',
                insertText      : 'Enum_Order_Execute()',
                detail          : '# 返回订单类型行权单的枚举值\n' +
                                  '    char Enum_Order_Execute()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Abandon()',
                insertText      : 'Enum_Order_Abandon()',
                detail          : '# 返回订单类型弃权单的枚举值\n' +
                                  '    char Enum_Order_Abandon()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Enquiry()',
                insertText      : 'Enum_Order_Enquiry()',
                detail          : '# 返回订单类型询价单的枚举值\n' +
                                  '    char Enum_Order_Enquiry()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Offer()',
                insertText      : 'Enum_Order_Offer()',
                detail          : '# 返回订单类型应价单的枚举值\n' +
                                  '    char Enum_Order_Offer()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Iceberg()',
                insertText      : 'Enum_Order_Iceberg()',
                detail          : '# 返回订单类型冰山单的枚举值\n' +
                                  '    char Enum_Order_Iceberg()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Ghost()',
                insertText      : 'Enum_Order_Ghost()',
                detail          : '# 返回订单类型影子单的枚举值\n' +
                                  '    char Enum_Order_Ghost()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_Swap()',
                insertText      : 'Enum_Order_Swap()',
                detail          : '# 返回订单类型互换单的枚举值\n' +
                                  '    char Enum_Order_Swap()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_SpreadApply()',
                insertText      : 'Enum_Order_SpreadApply()',
                detail          : '# 返回订单类型套利申请的枚举值\n' +
                                  '    char Enum_Order_SpreadApply()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_HedgApply()',
                insertText      : 'Enum_Order_HedgApply()',
                detail          : '# 返回订单类型套保申请的枚举值\n' +
                                  '    char Enum_Order_HedgApply()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_OptionAutoClose()',
                insertText      : 'Enum_Order_OptionAutoClose()',
                detail          : '# 返回订单类型行权前期权自对冲申请的枚举值\n' +
                                  '    char Enum_Order_OptionAutoClose()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_FutureAutoClose()',
                insertText      : 'Enum_Order_FutureAutoClose()',
                detail          : '# 返回订单类型履约期货自对冲申请的枚举值\n' +
                                  '    char Enum_Order_FutureAutoClose()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Order_MarketOptionKeep()',
                insertText      : 'Enum_Order_MarketOptionKeep()',
                detail          : '# 返回订单类型做市商留仓的枚举值\n' +
                                  '    char Enum_Order_MarketOptionKeep()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_GFD()',
                insertText      : 'Enum_GFD()',
                detail          : '# 返回订单有效类型当日有效的枚举值\n' +
                                  '    char Enum_GFD()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_GTC()',
                insertText      : 'Enum_GTC()',
                detail          : '# 返回订单有效类型当日有效的枚举值\n' +
                                  '    char Enum_GTC()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_GTD()',
                insertText      : 'Enum_GTD()',
                detail          : '# 返回订单有效类型限期有效的枚举值\n' +
                                  '    char Enum_GTD()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_IOC()',
                insertText      : 'Enum_IOC()',
                detail          : '# 返回订单有效类型即时部分有效的枚举值\n' +
                                  '    char Enum_IOC()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_FOK()',
                insertText      : 'Enum_FOK()',
                detail          : '# 返回订单有效类型即时全部有效的枚举值\n' +
                                  '    char Enum_FOK()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Speculate()',
                insertText      : 'Enum_Speculate()',
                detail          : '# 返回订单投保标记投机的枚举值\n' +
                                  '    char Enum_Speculate()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Hedge()',
                insertText      : 'Enum_Hedge()',
                detail          : '# 返回订单投保标记套保的枚举值\n' +
                                  '    char Enum_Hedge()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Spread()',
                insertText      : 'Enum_Spread()',
                detail          : '# 返回订单投保标记套利的枚举值\n' +
                                  '    char Enum_Spread()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Market()',
                insertText      : 'Enum_Market()',
                detail          : '# 返回订单投保标记做市的枚举值\n' +
                                  '    char Enum_Market()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Close()',
                insertText      : 'Enum_Data_Close()',
                detail          : '# 返回收盘价的枚举值\n' +
                                  '    char Enum_Data_Close()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Open()',
                insertText      : 'Enum_Data_Open()',
                detail          : '# 返回开盘价的枚举值\n' +
                                  '    char Enum_Data_Open()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_High()',
                insertText      : 'Enum_Data_High()',
                detail          : '# 返回最高价的枚举值\n' +
                                  '    char Enum_Data_High()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Low()',
                insertText      : 'Enum_Data_Low()',
                detail          : '# 返回最低价的枚举值\n' +
                                  '    char Enum_Data_Low()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Median()',
                insertText      : 'Enum_Data_Median()',
                detail          : '# 返回中间价的枚举值，中间价=（最高价+最低价）/ 2\n' +
                                  '    char Enum_Data_Median()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Typical()',
                insertText      : 'Enum_Data_Typical()',
                detail          : '# 返回标准价的枚举值，标准价=（最高价+最低价+收盘价）/ 3\n' +
                                  '    char Enum_Data_Typical()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Weighted()',
                insertText      : 'Enum_Data_Weighted()',
                detail          : '# 返回加权收盘价的枚举值，加权收盘价=（最高价+最低价+开盘价+收盘价）/ 4\n' +
                                  '    char Enum_Data_Weighted()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Vol()',
                insertText      : 'Enum_Data_Vol()',
                detail          : '# 返回成交量的枚举值\n' +
                                  '    char Enum_Data_Vol()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Opi()',
                insertText      : 'Enum_Data_Opi()',
                detail          : '# 返回持仓量的枚举值\n' +
                                  '    char Enum_Data_Opi()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'Enum_Data_Time()',
                insertText      : 'Enum_Data_Time()',
                detail          : '# 返回K线时间的枚举值\n' +
                                  '    char Enum_Data_Time()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符',
                kind            : monaco.languages.CompletionItemKind.Enum
            },{
                label           : 'SetUserNo(userNo)',
                insertText      : 'SetUserNo(${1})',
                detail          : '# 设置实盘交易账户\n' +
                                  '    int SetUserNo(string userNo)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    userNo 实盘交易账户，不能为空字符串\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型, 0成功，-1失败\n' +
                                  '    若需要添加多个不同的交易账号，则可多次调用该账户\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetUserNo(\'ET001\')',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetBarInterval(contractNo, barType, barInterval, sampleConfig=2000)',
                insertText      : 'SetBarInterval(${1})',
                detail          : '# 设置指定合约的K线类型和K线周期，以及策略历史回测的起始点信息\n' +
                                  '    int SetBarInterval(string contractNo, char barType, int barInterval, int|string|char sampleConfig=2000)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '    barType K线类型 T分笔，M分钟，D日线\n' +
                                  '    barInterval K线周期\n' +
                                  '    sampleConfig 策略历史回测的起始点信息，可选的值为：\n' +
                                  '    字符A : 使用所有K线\n' +
                                  '    字符N : 不执行历史K线\n' +
                                  '    整数 : 历史回测使用的K线根数\n' +
                                  '    字符串 : 用于历史回测样本的起始日期，格式为YYYYMMDD，精确到日，例如2019-04-30的日期格式为\'20190430\'\n' +
                                  '    默认为使用2000根K线进行回测\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型, 0成功，-1失败\n' +
                                  '    通过该方法系统会订阅指定合约的K线数据，\n' +
                                  '    对于相同的合约，如果使用该函数设置不同的K线类型(barType)和周期(barInterval)，则系统会同时订阅指定的K线类型和周期的行情数据\n' +
                                  '    如果使用该方法订阅了多个合约，则第一条合约为基准合约\n' +
                                  '    如果在策略中使用SetBarInterval方法订阅了合约，则在设置界面选中的基准合约便不再订阅\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetBarInterval(\'ZCE|F|SR|906\', \'M\', 3, \'A\') 订阅合约ZCE|F|SR|906的3分钟K线数据，并使用所有K线样本进行历史回测\n' +
                                  '    SetBarInterval(\'ZCE|F|SR|906\', \'M\', 3, \'N\') 订阅合约ZCE|F|SR|906的3分钟K线数据，并不使用K线样本进行历史回测\n' +
                                  '    SetBarInterval(\'ZCE|F|SR|906\', \'M\', 3, 2000) 订阅合约ZCE|F|SR|906的3分钟K线数据，并使用2000根K线样本进行历史回测\n' +
                                  '    SetBarInterval(\'ZCE|F|SR|906\', \'M\', 3) 订阅合约ZCE|F|SR|906的3分钟K线数据，由于sampleConfig的默认值为2000，所以使用2000根K线样本进行历史回测\n' +
                                  '    SetBarInterval(\'ZCE|F|SR|906\', \'M\', 3, \'20190430\') 订阅合约ZCE|F|SR|906的3分钟K线数据，并使用2019-04-30起的K线进行历史回测',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetSample(sampleType, int|string sampleValue)',
                insertText      : 'SetSample(${1})',
                detail          : '# 设置策略历史回测的样本数量，默认为使用2000根K线进行回测。\n' +
                                  '    int SetSample(char sampleType, int|string sampleValue)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    sampleType 历史回测起始点类型\n' +
                                  '    A : 使用所有K线\n' +
                                  '    D : 指定日期开始触发\n' +
                                  '    C : 使用固定根数\n' +
                                  '    N : 不执行历史K线\n' +
                                  '    sampleValue 可选，设置历史回测起始点使用的数值\n' +
                                  '    当sampleType为A或N时，sampleValue的值不设置；\n' +
                                  '    当sampleType为D时，sampleValue为形如\'20190430\'的string型触发指定日期；\n' +
                                  '    当sampleType为C时，sampleValue为int型历史回测使用的K线根数。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetInitCapital(capital=10000000)',
                insertText      : 'SetInitCapital(${1})',
                detail          : '# 设置初始资金，不设置默认100万\n' +
                                  '    int SetInitCapital(float capital=10000000)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    capital 初始资金，默认为10000000\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetInitCapital(200*10000), 设置初始资金为200万',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetMargin(type, value=0, contractNo=\'\')',
                insertText      : 'SetMargin(${1})',
                detail          : '# 设置保证金参数，不设置或设置失败取界面设置的保证金比例\n' +
                                  '    int SetMargin(float type, float value=0, string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    type 0：按比例收取保证金， 1：按定额收取保证金，\n' +
                                  '    value 按比例收取保证金时的比例， 或者按定额收取保证金时的额度，\n' +
                                  '    contractNo 合约编号，默认为基础合约。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetMargin(0, 0.08) 设置基础合约的保证金按比例收取8%\n' +
                                  '    SetMargin(1, 80000, \'ZCE|F|SR|906\') 设置合约ZCE|F|SR|906的保证金按额度收取80000',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetTradeFee(type, feeType, feeValue, contractNo=\'\')',
                insertText      : 'SetTradeFee(${1})',
                detail          : '# 设置手续费收取方式\n' +
                                  '    int SetTradeFee(string type, int feeType, float feeValue, string contractNo=\'\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    type 手续费类型，A-全部，O-开仓，C-平仓，T-平今\n' +
                                  '    feeType 手续费收取方式，1-按比例收取，2-按定额收取\n' +
                                  '    feeValue 按比例收取手续费时，feeValue为收取比例；按定额收取手续费时，feeValue为收取额度\n' +
                                  '    contractNo 合约编号，默认为基础合约\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetTradeFee(\'O\', 2， 5) 设置基础合约的开仓手续费为5元/手\n' +
                                  '    SetTradeFee(\'O\', 1， 0.02) 设置基础合约的开仓手续费为每笔2%\n' +
                                  '    SetTradeFee(\'T\', 2， 5, \"ZCE|F|SR|906\") 设置合约ZCE|F|SR|906的平今手续费为5元/手',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetActual()',
                insertText      : 'SetActual()',
                detail          : '# 设置策略在实盘上运行\n' +
                                  '    int SetActual()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'SetOrderWay(type)',
                insertText      : 'SetOrderWay(${1})',
                detail          : '# 设置发单方式\n' +
                                  '    int SetOrderWay(int type)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    type 在实盘上的发单方式，1 表示实时发单,2 表示K线完成后发单\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetOrderWay(1)    # 在实盘上使用实时数据运行策略，实时发单\n' +
                                  '    SetOrderWay(2)     # 在实盘上使用实时数据运行策略，在K线稳定后发单',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetTradeDirection(tradeDirection)',
                insertText      : 'SetTradeDirection(${1})',
                detail          : '# 设置交易方向\n' +
                                  '    int SetTradeDirection(int tradeDirection)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    tradeDirection 设置交易方向\n' +
                                  '    0 : 双向交易\n' +
                                  '    1 : 仅多头\n' +
                                  '    2 : 仅空头\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetTradeDirection(0)    # 双向交易',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetMinTradeQuantity(tradeQty=1)',
                insertText      : 'SetMinTradeQuantity(${1})',
                detail          : '# 设置最小下单量，单位为手，默认值为1手。\n' +
                                  '    int SetMinTradeQuantity(int tradeQty=1)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    tradeQty 最小下单量，默认为1，不超过1000\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetHedge(hedge)',
                insertText      : 'SetHedge(${1})',
                detail          : '# 设置投保标志\n' +
                                  '    int SetHedge(char hedge)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    hedge 投保标志\n' +
                                  '    T : 投机\n' +
                                  '    B : 套保\n' +
                                  '    S : 套利\n' +
                                  '    M : 做市\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetHedge(\'T\') # 设置基础合约的投保标志为投机',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetSlippage(slippage)',
                insertText      : 'SetSlippage(${1})',
                detail          : '# 设置滑点损耗\n' +
                                  '    int SetSlippage(float slippage)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    slippage 滑点损耗\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetTriggerType(type, int|list value=None)',
                insertText      : 'SetTriggerType(${1})',
                detail          : '# 设置触发方式\n' +
                                  '    int SetTriggerType(int type, int|list value=None)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    type 触发方式，可使用的值为：\n' +
                                  '    1 : 即时行情触发\n' +
                                  '    2 : 交易数据触发\n' +
                                  '    3 : 每隔固定时间触发\n' +
                                  '    4 : 指定时刻触发\n' +
                                  '    5 : K线触发\n' +
                                  '    value 当触发方式是为每隔固定时间触发(type=3)时，value为触发间隔，单位为毫秒，必须为100的整数倍，\n' +
                                  '    当触发方式为指定时刻触发(type=4)时，value为触发时刻列表，时间的格式为\'20190511121314\'\n' +
                                  '    当type为其他值时，该值无效，可以不填\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetTriggerType(3, 1000) # 每隔1000毫秒触发一次\n' +
                                  '    SetTriggerType(4, [\'084000\', \'084030\', \'084100\']) # 指定时刻触发',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetWinPoint(winPoint, nPriceType=0, nAddTick=0, contractNo=\"\")',
                insertText      : 'SetWinPoint(${1})',
                detail          : '# 设置触发方式\n' +
                                  '    SetWinPoint(int winPoint, int nPriceType = 0, int nAddTick = 0, string contractNo = \"\")\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    winPoint 赢利点数值，若当前价格相对于最近一次开仓价格的盈利点数达到或超过该值，就进行止盈；\n' +
                                  '    nPriceType 平仓下单价格类型 0:最新价 1：对盘价 2：挂单价 3：市价 4：停板价，默认值为0；\n' +
                                  '    nAddTick 超价点数 仅当nPrice为0，1，2时有效，默认为0；\n' +
                                  '    contractNo 合约代码，默认为基准合约。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetWinPoint(10) # 当价格相对于最近一次开仓价格超过10个点，进行止盈平仓。如郑棉合约多头：开仓价格为15000，当前价格大于或等于5*10=50时，即达到15050，则进行平仓。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetWinPoint(stopPoint, nPriceType=0, nAddTick=0, contractNo=\"\")',
                insertText      : 'SetStopPoint(${1})',
                detail          : '# 设置触发方式\n' +
                                  '    SetWinPoint(int stopPoint, int nPriceType = 0, int nAddTick = 0, string contractNo = \"\")\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    stopPoint 止损点数，若当前价格相对于最近一次开仓价格亏损点数达到或跌破该值，就进行止损；\n' +
                                  '    nPriceType 平仓下单价格类型 0:最新价 1：对盘价 2：挂单价 3：市价 4：停板价，默认值为0；\n' +
                                  '    nAddTick 超价点数 仅当nPrice为0，1，2时有效，默认为0；\n' +
                                  '    contractNo 合约代码，默认为基准合约。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetStopPoint(10) # 当价格跌破10个点，进行止损平仓。 如：如郑棉合约多头：开仓价格为15000，当前价格小于或等于5*10=50时，即达到14950，则进行平仓。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetFloatStopPoint(startPoint, stopPoint, nPriceType=0, nAddTick=0, contractNo=\"\")',
                insertText      : 'SetFloatStopPoint(${1})',
                detail          : '# 设置触发方式\n' +
                                  '    int SetFloatStopPoint(int startPoint, int stopPoint, int nPriceType = 0, int nAddTick = 0, string contractNo = \"\")\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    startPoint 启动点数，当前价格相对于最后一次开仓价格盈利点数超过该值后启动浮动止损监控；\n' +
                                  '    stopPoint 止损点数，若当前价格相对于最近一次开仓价格亏损点数达到或跌破该值，就进行止损；\n' +
                                  '    nPriceType 平仓下单价格类型 0:最新价 1：对盘价 2：挂单价 3：市价 4：停板价，默认为0；\n' +
                                  '    nAddTick 超价点数 仅当nPrice为0，1，2时有效，默认为0；\n' +
                                  '    contractNo 合约代码，默认为基准合约。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SetFloatStopPoint(20,10)\n' +
                                  '    举例：郑棉合约，多头方向。开仓价格为15000，当前价格突破15100后开启浮动止损，若此，止损点会随着价格上升而不断上升。假如价格上涨到15300，则此时的止损价格为(15300-50),即15250，若价格从15300回落到15250，则进行自动平仓。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SetStopWinKtBlack(op, kt)',
                insertText      : 'SetStopWinKtBlack(${1})',
                detail          : '# 设置不触发止损止盈和浮动止损的K线类型\n' +
                                  '    int SetStopWinKtBlack(op, kt)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    op  操作类型必须为 0: 取消设置, 1: 增加设置，中的一个\n' +
                                  '    kt  K线类型必须为 \'D\', \'M\', \'T\'，中的一个\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，0成功，-1失败',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'GetStopWinKtBlack()',
                insertText      : 'GetStopWinKtBlack()',
                detail          : '# 获取不触发止损止盈和浮动止损的K线类型列表\n' +
                                  '    list GetStopWinKtBlack()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回不触发止损/止盈/浮动止损的K线类型列表',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'SubQuote(contractNo1, contractNo2, contractNo3, ...)',
                insertText      : 'SubQuote(${1})',
                detail          : '# 订阅指定合约的即时行情。\n' +
                                  '    bool SubQuote(string contractNo1, string contractNo2, string contractNo3, ...)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号，为空不做任何操作\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该方法可用策略中的initialize(context)方法中订阅指定合约的即时行情，也可在handle_data(context)方法中动态的订阅指定合约的即使行情。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SubQuote(\"ZCE|F|TA|909\") 订阅合约TA909的即时行情；\n' +
                                  '    SubQuote(\"ZCE|F|TA|909\", \"ZCE|F|TA|910\") 订阅合约TA909和TA910的即时行情；\n' +
                                  '    SubQuote(\"ZCE|F|TA\") 订阅TA品种下所有合约的即时行情',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnsubQuote(contractNo1, contractNo2, contractNo3, ...)',
                insertText      : 'UnsubQuote(${1})',
                detail          : '# 退订指定合约的即时行情。\n' +
                                  '    bool UnsubQuote(string contractNo1, string contractNo2, string contractNo3, ...)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    contractNo 合约编号\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该方法可用策略中的initialize(context)方法中退订指定合约的即时行情，也可在handle_data(context)方法中动态的退订指定合约的即使行情。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnsubQuote(\'ZCE|F|SR|909\') 退订合约\'ZCE|F|SR|909\'的即时行情；\n' +
                                  '    UnsubQuote(\'ZCE|F|SR|909\', \'ZCE|F|SR|910\') 退订合约\'ZCE|F|SR|909\'和\'ZCE|F|SR|910\'的即时行情；\n' +
                                  '    UnsubQuote(\'ZCE|F|SR\') 退订合约商品\'ZCE|F|SR\'对应的所有合约的即时行情。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotNumeric(name,float value,int color,bool main, axis, barsback=0)',
                insertText      : 'PlotNumeric(${1})',
                detail          : '# 在当前Bar输出一个数值\n' +
                                  '    float PlotNumeric(string name,float value,int color,bool main, char axis, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name  输出值的名称，不区分大小写；\n' +
                                  '    value 输出的数值；\n' +
                                  '    color 输出值的显示颜色，默认表示使用属性设置框中的颜色；\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    axis  指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出一个数值，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    例1：PlotNumeric (\"MA1\",Ma1Value);\n' +
                                  '    输出MA1的值。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotIcon(Value,int Icon, main, barsback=0)',
                insertText      : 'PlotIcon(${1})',
                detail          : '# 在当前Bar输出一个图标\n' +
                                  '    float PlotIcon(float Value,int Icon, bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    value 输出的值\n' +
                                  '    icon 图标类型，0-默认图标，1-笑脸，2-哭脸，3-上箭头，4-下箭头，5-上箭头2, 6-下箭头2\n' +
                                  '    7-喇叭，8-加锁，9-解锁，10-货币+，11-货币-，12-加号，13-减号，14-叹号，15-叉号\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出一个数值，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    例1：PlotIcon(10,14);\n' +
                                  '    输出MA1的值。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotDot(name, value, icon, color, main, barsback=0)',
                insertText      : 'PlotDot(${1})',
                detail          : '# 在当前Bar输出一个点\n' +
                                  '    PlotDot(string name, float value, int icon, int color, bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    value 输出的值\n' +
                                  '    icon  图标类型0-14，共15种样式，包括箭头，圆点，三角等\n' +
                                  '    color 输出值的显示颜色，默认表示使用属性设置框中的颜色；\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出一个数值，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    PlotDot(name=\"Dot\", value=Close()[-1], main=True)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotBar(name, vol1, vol2, color, main, filled, barsback=0)',
                insertText      : 'PlotBar(${1})',
                detail          : '# 绘制一根Bar\n' +
                                  '    PlotBar(string name, int vol1, int vol2, int color, bool main, bool filled, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name  bar名称\n' +
                                  '    vol1  柱子起始点\n' +
                                  '    vol2  柱子结束点\n' +
                                  '    color 输出值的显示颜色，默认表示使用属性设置框中的颜色；\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    filled 是否填充, 默认填充\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出一个数值，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    PlotBar(\"BarExample1\", Vol()[-1], 0, RGB_Red())',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotText(value, text, color, main, barsback=0)',
                insertText      : 'PlotText(${1})',
                detail          : '# 在当前Bar输出字符串\n' +
                                  '    PlotText(stirng value, string text, int color, bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    value 输出的价格\n' +
                                  '    text 输出的字符串，最多支持19个英文字符\n' +
                                  '    color 输出值的显示颜色，默认表示使用属性设置框中的颜色；\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出字符串，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    例1：PlotText(\"ORDER\");',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotVertLine(color, main, axis, barsback=0)',
                insertText      : 'PlotVertLine(${1})',
                detail          : '# 在当前Bar输出一个竖线\n' +
                                  '    float PlotVertLine(color, bool main, bool axis, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    color 输出值的显示颜色，默认表示使用属性设置框中的颜色；\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    axis  指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出一个数值，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    PlotVertLine(main=True, axis = True)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotPartLine(name, index1, price1, count, price2, color, main, axis, width)',
                insertText      : 'PlotPartLine(${1})',
                detail          : '# 绘制斜线段\n' +
                                  '    PlotPartLine(string name, int index1, float price1, int count, float price2, int color, bool main, bool axis, int width)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name   名称\n' +
                                  '    index1 起始bar索引\n' +
                                  '    price1 起始价格\n' +
                                  '    count  从起始bar回溯到结束bar的根数\n' +
                                  '    price2 结束价格\n' +
                                  '    color  输出值的显示颜色，默认表示使用属性设置框中的颜色；\n' +
                                  '    main   指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    axis   指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标\n' +
                                  '    width  线段宽度，默认1\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出一个数值，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    idx1 = CurrentBar()\n' +
                                  '    p1 = Close()[-1]\n' +
                                  '    if idx1 >= 100:\n' +
                                  '    count = 1\n' +
                                  '    p2 = Close()[-2]\n' +
                                  '    PlotPartLine(\"PartLine\", idx1, p1, count, p2, RGB_Red(), True, True, 1)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PlotStickLine(name, price1, price2, color, main, axis, barsback=0)',
                insertText      : 'PlotStickLine(${1})',
                detail          : '# 绘制竖线段\n' +
                                  '    PlotStickLine(string name, float price1, float price2, int color, bool main, bool axis, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name   名称\n' +
                                  '    price1 起始价格\n' +
                                  '    price2 结束价格\n' +
                                  '    color 输出值的显示颜色，默认表示使用属性设置框中的颜色；\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    axis  指标是否使用独立坐标，True-独立坐标，False-非独立坐标，默认非独立坐标\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    在当前Bar输出一个数值，输出的值用于在上层调用模块显示。返回数值型，即输入的Number。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    PlotStickLine(\"StickLine\", Close()[-1], Open()[-1], RGB_Blue(), True, True, 0)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotText(bool main, barsback=0)',
                insertText      : 'UnPlotText(${1})',
                detail          : '# 在当前Bar取消输出的字符串\n' +
                                  '    UnPlotText(bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotText();',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotIcon(bool main, barsback=0)',
                insertText      : 'UnPlotIcon(${1})',
                detail          : '# 在当前Bar取消输出的Icon\n' +
                                  '    UnPlotIcon(bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotIcon();',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotVertLine(bool main, barsback=0)',
                insertText      : 'UnPlotVertLine(${1})',
                detail          : '# 在当前Bar取消输出的竖线\n' +
                                  '    UnPlotVertLine(bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotVertLine();',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotDot(bool main, barsback=0)',
                insertText      : 'UnPlotDot(${1})',
                detail          : '# 在当前Bar取消输出的Dot\n' +
                                  '    UnPlotDot(bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name  名称\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotDot();',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotBar(name, main, barsback=0)',
                insertText      : 'UnPlotBar(${1})',
                detail          : '# 在当前Bar取消输出的Bar\n' +
                                  '    UnPlotBar(string name, bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name  名称\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotBar(“Bar”);',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotNumeric(name, main, barsback=0)',
                insertText      : 'UnPlotNumeric(${1})',
                detail          : '# 在当前Bar取消输出的Numeric\n' +
                                  '    UnPlotNumeric(string name, bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name  名称\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotNumeric(\"numeric\")',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotPartLine(name, index1, count, main)',
                insertText      : 'UnPlotPartLine(${1})',
                detail          : '# 在当前Bar取消输出的斜线段\n' +
                                  '    UnPlotPartLine(string name, int index1, int count, bool main)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name  名称\n' +
                                  '    index1 起始bar索引\n' +
                                  '    count  从起始bar回溯到结束bar的根数\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotPartLine(\"PartLine\", idx1, count, True)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'UnPlotStickLine(name, main, barsback=0)',
                insertText      : 'UnPlotStickLine(${1})',
                detail          : '# 在当前Bar取消输出的竖线段\n' +
                                  '    UnPlotStickLine(string name, bool main, int barsback=0)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    name  名称\n' +
                                  '    main  指标是否加载到主图，True-主图，False-幅图，默认主图\n' +
                                  '    barsback 从当前Bar向前回溯的Bar数，默认值为当前Bar。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    UnPlotStickLine(\"StickLine\")',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LogDebug(args)',
                insertText      : 'LogDebug(${1})',
                detail          : '# 在运行日志窗口中打印用户指定的调试信息。\n' +
                                  '    LogDebug(args)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    accountId = A_AccountID()\n' +
                                  '    LogDebug(\"当前使用的用户账户ID为 : \", accountId)\n' +
                                  '    available = A_Available()\n' +
                                  '    LogDebug(\"当前使用的用户账户ID为 : %s，可用资金为 : %10.2f\" % (accountId, available))',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LogInfo(args)',
                insertText      : 'LogInfo(${1})',
                detail          : '# 在运行日志窗口中打印用户指定的普通信息。\n' +
                                  '    LogInfo(args)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    accountId = A_AccountID()\n' +
                                  '    LogInfo(\"当前使用的用户账户ID为 : \", accountId)\n' +
                                  '    available = A_Available()\n' +
                                  '    LogInfo(\"当前使用的用户账户ID为 : %s，可用资金为 : %10.2f\" % (accountId, available))',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LogWarn(args)',
                insertText      : 'LogWarn(${1})',
                detail          : '# 在运行日志窗口中打印用户指定的警告信息。\n' +
                                  '    LogWarn(args)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    accountId = A_AccountID()\n' +
                                  '    LogWarn(\"当前使用的用户账户ID为 : \", accountId)\n' +
                                  '    available = A_Available()\n' +
                                  '    LogWarn(\"当前使用的用户账户ID为 : %s，可用资金为 : %10.2f\" % (accountId, available))',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LogError(args)',
                insertText      : 'LogError(${1})',
                detail          : '# 在运行日志窗口中打印用户指定的错误信息。\n' +
                                  '    LogError(args)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    args 用户需要打印的内容，如需要在运行日志窗口中输出多个内容，内容之间用英文逗号分隔。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    accountId = A_AccountID()\n' +
                                  '    LogError(\"当前使用的用户账户ID为 : \", accountId)\n' +
                                  '    available = A_Available()\n' +
                                  '    LogError(\"当前使用的用户账户ID为 : %s，可用资金为 : %10.2f\" % (accountId, available))',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SMA(self, numpy.array price, period, weight)',
                insertText      : 'SMA(${1})',
                detail          : '# 获取加权移动平均值\n' +
                                  '    SMA(self, numpy.array price, int period, int weight)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    price   序列值，numpy数组\n' +
                                  '    period  周期\n' +
                                  '    weight  权重\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回值为浮点型numpy.array；\n' +
                                  '    如果计算成功，此时返回值是计算出的sma值序列；\n' +
                                  '    如果计算失败，此时返回值numpy.array为空\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SMA(Close(), 12, 2)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'REF(Price,int Length)',
                insertText      : 'REF(${1})',
                detail          : '# 求N周期前数据的值\n' +
                                  '    float REF(float Price,int Length)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    Price   价格\n' +
                                  '    Length  需要计算的周期数。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    Length不能小于0\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    REF(Close, 1); 获得上一周期的收盘价，等价于Close[-2]\n' +
                                  '    REF((Close + High + Low)/ 3, 10); 返回10周期前的高低收价格的平均值。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ParabolicSAR(self, numpy.array high, numpy.array low, afstep, aflimit)',
                insertText      : 'ParabolicSAR(${1})',
                detail          : '# 计算抛物线转向\n' +
                                  '    ParabolicSAR(self, numpy.array high, numpy.array low, float afstep, float aflimit)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    high    最高价序列值，numpy数组\n' +
                                  '    low     最低价序列值，numpy数组\n' +
                                  '    afstep  加速因子\n' +
                                  '    aflimit 加速因子的限量\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回值为四个值，均为数值型numpy.array\n' +
                                  '    第一个值序列为oParClose,当前bar的停损值；\n' +
                                  '    第二个值序列为oParOpen, 下一Bar的停损值；\n' +
                                  '    第三个值序列为oPosition，输出建议的持仓状态，1 - 买仓，-1 - 卖仓；\n' +
                                  '    第四个值序列为oTransition, 输出当前Bar的状态是否发生反转，1 或 -1 为反转，0 为保持不变。\n' +
                                  '    当输入high,low的numpy数组为空时，计算失败，返回的四个值均为空的numpy.array\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    ParabolicSAR(High(), Low(), 0.02, 0.2)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Highest(list|numpy.array price, length)',
                insertText      : 'Highest(${1})',
                detail          : '# 求最高\n' +
                                  '    numpy.array Highest(list|numpy.array price, int length)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    price 用于求最高值的值，必须是数值型列表；\n' +
                                  '    length 需要计算的周期数，为整型。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该函数计算指定周期内的数值型序列值的最高值，返回值为浮点数数字列表;\n' +
                                  '    当price的类型不是list或者price的长度为0时，则返回为空的numpy.array()\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    Highest (Close(), 12); 计算12周期以来的收盘价的最高值；\n' +
                                  '    Highest (HisData(Enum_Data_Typical()), 10); 计算10周期以来高低收价格的平均值的最高值。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Lowest(list|numpy.array price, length)',
                insertText      : 'Lowest(${1})',
                detail          : '# 求最低\n' +
                                  '    numpy.array Lowest(list|numpy.array price, int length)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    price 用于求最低值的值，必须是数值型列表；\n' +
                                  '    length 需要计算的周期数，为整型。\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该函数计算指定周期内的数值型序列值的最低值，返回值为浮点数数字列表;\n' +
                                  '    当price的类型不是list或者price的长度为0时，则返回为空的numpy.array()\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    Highest (Close(), 12); 计算12周期以来的收盘价的最低值；\n' +
                                  '    Lowest (HisData(Enum_Data_Typical()), 10); 计算10周期以来高低收价格的平均值的最低值。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CountIf(condition, period):',
                insertText      : 'CountIf(${1})',
                detail          : '# 获取最近N周期条件满足的计数\n' +
                                  '    int CountIf(condition, period):\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    condition 传入的条件表达式；\n' +
                                  '    period 计算条件的周期数\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    获取最近N周期条件满足的计数\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    CountIf(Close() >Open() , 10); 最近10周期出现Close>Open的周期总数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CrossOver(Price1, Price2)',
                insertText      : 'CrossOver(${1})',
                detail          : '# 求是否上穿\n' +
                                  '    Bool CrossOver(np.array Price1, np.array Price2)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    Price1 求相关系统的数据源1，必须是np数组;\n' +
                                  '    Price2 求相关系统的数据源2，必须是np数组;\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该函数返回Price1数值型序列值是否上穿Price2数值型序列值，返回值为布尔型。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    CrossOver(Close[1], AvgPrice); 判断上一个Bar的收盘价Close是否上穿AvgPrice.\n' +
                                  '    注意：在使用判断穿越的函数时，要尽量避免使用例如close等不确定的元素，否则会导致信号消失，\n' +
                                  '    一般情况下，Close可以改用High和Low分别判断向上突破（函数CrossOver）和向下突破（函数CrossUnder）。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CrossUnder(Price1, Price2)',
                insertText      : 'CrossUnder(${1})',
                detail          : '# 求是否下破\n' +
                                  '    Bool CrossUnder(np.array Price1, np.array Price2)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    Price1 求相关系统的数据源1，必须是np数组;\n' +
                                  '    Price2 求相关系统的数据源2，必须是np数组;\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该函数返回Price1数值型序列值是否上穿Price2数值型序列值，返回值为布尔型。\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    CrossOver(Close[1], AvgPrice); 判断上一个Bar的收盘价Close是否上穿AvgPrice.\n' +
                                  '    注意：在使用判断穿越的函数时，要尽量避免使用例如close等不确定的元素，否则会导致信号消失，\n' +
                                  '    一般情况下，Close可以改用High和Low分别判断向上突破（函数CrossOver）和向下突破（函数CrossUnder）。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SwingHigh(Price, Length, Instance, Strength)',
                insertText      : 'SwingHigh(${1})',
                detail          : '# 求波峰点\n' +
                                  '    float SwingHigh(np.array Price, int Length, int Instance, int Strength)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    Price 用于求波峰点的值，必须是np数组或者序列变量\n' +
                                  '    Length 是需要计算的周期数，为整型\n' +
                                  '    Instance 设置返回哪一个波峰点，1 - 最近的波峰点，2 - 倒数第二个，以此类推\n' +
                                  '    Strength 设置转折点两边的需要的周期数，必须小于Length；\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该函数计算指定周期内的数值型序列值的波峰点，返回值为浮点数;\n' +
                                  '    当序列值的CurrentBar小于Length时，该函数返回-1.0\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SwingHigh(Close, 10, 1, 2);计算Close在最近10个周期的波峰点的值，最高点两侧每侧至少需要2个Bar。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SwingLow(Price, Length, Instance, Strength)',
                insertText      : 'SwingLow(${1})',
                detail          : '# 求波谷点\n' +
                                  '    float SwingLow(np.array Price, int Length, int Instance, int Strength)\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    Price 用于求波峰点的值，必须是np数组或者序列变量\n' +
                                  '    Length 是需要计算的周期数，为整型\n' +
                                  '    Instance 设置返回哪一个波峰点，1 - 最近的波谷点，2 - 倒数第二个，以此类推\n' +
                                  '    Strength 设置转折点两边的需要的周期数，必须小于Length；\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    该函数计算指定周期内的数值型序列值的波谷点，返回值为浮点数;\n' +
                                  '    当序列值的CurrentBar小于Length时，该函数返回-1.0\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    SwingLow(Close, 10, 1, 2);计算Close在最近10个周期的波谷点的值，最低点两侧需要至少2个Bar。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'Alert(Info, bKeep=True, level=\'Signal\')',
                insertText      : 'Alert(${1})',
                detail          : '# 弹出警告提醒\n' +
                                  '    Alert(string Info, bool bKeep=True, string level=\'Signal\')\n' +
                                  '\n' +
                                  '参数：\n' +
                                  '    Info  提醒的内容\n' +
                                  '    bBeep 是否播放警告声音，默认为True\n' +
                                  '    level 声音类型, 包括\'Signal\'、\'Info\'、\'Warn\'、\'Error\'\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    多行提示信息需要自行换行，例如：\n' +
                                  '    AlertStr = \'合约: \' + contNo + \'\n' +
                                  '    \'                       \'方向: \' + self._bsMap[direct] + self._ocMap[offset] + \'\n' +
                                  '    \' +                       \'数量: \' + str(share) + \'\n' +
                                  '    \' +                       \'价格: \' + str(price) + \'\n' +
                                  '    \' +                       \'时间: \' + str(curBar[\'DateTimeStamp\']) + \'\n' +
                                  '    \'\n' +
                                  '\n' +
                                  '示例：\n' +
                                  '    Alert(\"Hello\"); 弹出提示',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'StrategyId()',
                insertText      : 'StrategyId()',
                detail          : '# 获取当前策略Id\n' +
                                  '    int StrategyId()',
                kind            : monaco.languages.CompletionItemKind.Function
            }
        ],


        ////////////////////////////////////////////////////////////////////////////////////////
        // context成员函数，输入context的时候出来
        //////////////////////////////////////////////////////////////////////////////////////// 
        'context':[
            {
                label           : 'strategyStatus()',
                insertText      : 'strategyStatus()',
                detail          : '# 获取当前策略状态\n' +
                                  '    strategyStatus()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符, \'H\' 表示回测阶段; \'C\' 表示实时数据阶段',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'triggerType()',
                insertText      : 'triggerType()',
                detail          : '# 获取当前触发类型\n' +
                                  '    triggerType()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符, \'T\' 定时触发; \'C\' 周期性触发; \'K\' 实时阶段K线触发; \'H\' 回测阶段K线触发; \'S\' 即时行情触发; \'O\' 委托状态变化触发 ; \'M\' 成交回报触发',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'contractNo()',
                insertText      : 'contractNo()',
                detail          : '# 获取当前触发合约\n' +
                                  '    contractNo()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串,例如: \'SHFE|F|CU|1907\'',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'kLineType()',
                insertText      : 'kLineType()',
                detail          : '# 获取当前触发的K线类型\n' +
                                  '    kLineType()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符, \'T\' 分笔; \'M\' 分钟; \'D\' 日线;',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'kLineSlice()',
                insertText      : 'kLineSlice()',
                detail          : '# 获取当前触发的K线周期\n' +
                                  '    kLineSlice()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回整型，例如1',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'tradeDate()',
                insertText      : 'tradeDate()',
                detail          : '# 获取当前触发的交易日\n' +
                                  '    tradeDate()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串, YYYYMMDD格式, \'20190524\'',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'dateTimeStamp()',
                insertText      : 'dateTimeStamp()',
                detail          : '# 获取当前触发的时间戳\n' +
                                  '    dateTimeStamp()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    返回字符串, YYYYMMDD格式, \'20190524\'',
                kind            : monaco.languages.CompletionItemKind.Function
            },{
                label           : 'triggerData()',
                insertText      : 'triggerData()',
                detail          : '# 获取当前触发类型对应的数据\n' +
                                  '    triggerData()\n' +
                                  '\n' +
                                  '备注：\n' +
                                  '    K线触发返回的是K线数据\n' +
                                  '    交易触发返回的是交易数据\n' +
                                  '    即时行情触发返回的是即时行情数据',
                kind            : monaco.languages.CompletionItemKind.Function
            }
        ],

        ////////////////////////////////////////////////////////////////////////////////////////
        // __code__ 字段，输入__code__.的时候出来
        //////////////////////////////////////////////////////////////////////////////////////// 
        '__code__':[
            {
                label           : 'co_argcount',
                insertText      : 'co_argcount',
                detail          : '# 函数接收参数的个数，不包括 *args 和 **kwargs 以及强制关键字参数',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_kwonlyargcount',
                insertText      : 'co_kwonlyargcount',
                detail          : '# 存放强制关键字参数的个数',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_nlocals',
                insertText      : 'co_nlocals',
                detail          : '# 函数中局部变量的个数，相当于是co_varnames的长度',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_stacksize',
                insertText      : 'co_stacksize',
                detail          : '# 一个整数，代表函数会使用的最大栈空间',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_flags',
                insertText      : 'co_flags',
                detail          : '# 这是一个整数，存放着函数的组合布尔标志位',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_code',
                insertText      : 'co_code',
                detail          : '# 二进制格式的字节码 bytecode，以字节串 bytes 的形式存储',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_consts',
                insertText      : 'co_consts',
                detail          : '# 在函数中用到的所有常量，比如整数、字符串、布尔值等等',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_names',
                insertText      : 'co_names',
                detail          : '# 该属性是由字符串组成的元组，里面按照使用顺序存放了全局变量和被导入的名字',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_varnames',
                insertText      : 'co_varnames',
                detail          : '# 函数所有的局部变量名称（包括函数参数）组成的元组, 顺序和实际可能不一致',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_freevars',
                insertText      : 'co_freevars',
                detail          : '# 元组里面存储着所有被函数使用的在闭包作用域中定义的变量名',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_cellvars',
                insertText      : 'co_cellvars',
                detail          : '# 元组里面存储着所有被嵌套函数用到的变量名',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_cell2arg',
                insertText      : 'co_cell2arg',
                detail          : '# 映射单元变量的参数',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_filename',
                insertText      : 'co_filename',
                detail          : '# 代码对象所在的文件名',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_name',
                insertText      : 'co_name',
                detail          : '# 是与代码对象关联的对象的名字',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_firstlineno',
                insertText      : 'co_firstlineno',
                detail          : '# 代码对象的第一行位于所在文件的行号',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_lnotab',
                insertText      : 'co_lnotab',
                detail          : '# 这个属性是line number table行号表的缩写。它以字节串bytes的形式存储，每两个字节是一对，分别是co_code字节串的偏移量和Python行号的偏移量',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_zombieframe',
                insertText      : 'co_zombieframe',
                detail          : '# 仅供优化',
                kind            : monaco.languages.CompletionItemKind.Field
            },{
                label           : 'co_weakreflist',
                insertText      : 'co_weakreflist',
                detail          : '# 第一个弱引用对象',
                kind            : monaco.languages.CompletionItemKind.Field
            }
        ],

        ////////////////////////////////////////////////////////////////////////////////////////
        // 类函数，输入.的时候出来
        ////////////////////////////////////////////////////////////////////////////////////////
        'sub':[
            {
                label           : '__new__',
                insertText      : '__new__(${1})',
                detail          : '# 类的实例化函数，在__init__之前调用',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__subclasses__',
                insertText      : '__subclasses__()',
                detail          : '# 获得所有子类',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__exit__',
                insertText      : '__exit__(${1})',
                detail          : '# with支持函数，with子代码块结束时被调用',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__enter__',
                insertText      : '__enter__(${1})',
                detail          : '# with支持函数，with子代码块开始时被调用',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__init__',
                insertText      : '__init__(${1})',
                detail          : '# 对象构造与初始化函数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__call__',
                insertText      : '__call__(${1})',
                detail          : '# ',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__import__',
                insertText      : '__import__(${1})',
                detail          : '# 用于动态加载类和函数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__del__',
                insertText      : '__del__(${1})',
                detail          : '# 虚构函数',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : '__name__',
                insertText      : '__name__',
                detail          : '# 名称',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__doc__',
                insertText      : '__doc__',
                detail          : '# 文档',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__members__',
                insertText      : '__members__',
                detail          : '# 数据成员',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__methods__',
                insertText      : '__methods__',
                detail          : '# 函数',
                kind            : monaco.languages.CompletionItemKind.Variable
            },{
                label           : '__code__',
                insertText      : '__code__',
                detail          : '# 二进制代码',
                kind            : monaco.languages.CompletionItemKind.Variable
            },
        ],

        ////////////////////////////////////////////////////////////////////////////////////////
        // talib函数，输入talib.或ta.的时候出来
        ////////////////////////////////////////////////////////////////////////////////////////
        'talib':[
            {
                label           : 'HT_DCPERIOD(close)',
                insertText      : 'HT_DCPERIOD(${1})',
                detail          : '# 希尔伯特变换-主导周期\n' +
                                  '    float HT_DCPERIOD(close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    将价格作为信息信号，计算价格处在的周期的位置，作为择时的依据',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HT_DCPHASE(close)',
                insertText      : 'HT_DCPHASE(${1})',
                detail          : '# 希尔伯特变换-主导循环阶段\n' +
                                  '    float HT_DCPHASE(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HT_PHASOR(close)',
                insertText      : 'HT_DCPHASE(${1})',
                detail          : '# 希尔伯特变换-希尔伯特变换相量分量\n' +
                                  '    inphase, quadrature = HT_PHASOR(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HT_SINE(close)',
                insertText      : 'HT_DCPHASE(${1})',
                detail          : '# 希尔伯特变换-正弦波\n' +
                                  '    sine, leadsine = HT_SINE(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HT_TRENDMODE(close)',
                insertText      : 'HT_DCPHASE(${1})',
                detail          : '# 希尔伯特变换-趋势与周期模式\n' +
                                  '    int HT_TRENDMODE(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ADD(high, low)',
                insertText      : 'ADD(${1})',
                detail          : '# 向量加法运算\n' +
                                  '    float ADD(high, low)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'DIV(high, low)',
                insertText      : 'DIV(${1})',
                detail          : '# 向量除法运算\n' +
                                  '    float DIV(high, low)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MAX(close, timeperiod=30)',
                insertText      : 'MAX(${1})',
                detail          : '# 周期内最大值\n' +
                                  '    float MAX(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MAXINDEX(close, timeperiod=30)',
                insertText      : 'MAXINDEX(${1})',
                detail          : '# 周期内最大值的索引\n' +
                                  '    int MAXINDEX(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MIN(close, timeperiod=30)',
                insertText      : 'MIN(${1})',
                detail          : '# 周期内最小值\n' +
                                  '    float MIN(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MININDEX(close, timeperiod=30)',
                insertText      : 'MININDEX(${1})',
                detail          : '# 周期内最小值的索引\n' +
                                  '    int MININDEX(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MINMAX(close, timeperiod=30)',
                insertText      : 'MINMAX(${1})',
                detail          : '# 周期内最小值和最大值(返回两个数组)\n' +
                                  '    min, max = MINMAX(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MINMAXINDEX(close, timeperiod=30)',
                insertText      : 'MINMAX(${1})',
                detail          : '# 周期内最小值和最大值索引(返回两个数组)\n' +
                                  '    minidx, maxidx = MINMAXINDEX(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MULT(high, low)',
                insertText      : 'MULT(${1})',
                detail          : '# 向量乘法运算\n' +
                                  '    float MULT(high, low)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SUB(high, low)',
                insertText      : 'SUB(${1})',
                detail          : '# 向量减法运算\n' +
                                  '    float SUB(high, low)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SUM(close, timeperiod=30)',
                insertText      : 'SUM(${1})',
                detail          : '# 周期内求和\n' +
                                  '    float SUM(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ACOS(close)',
                insertText      : 'ACOS(${1})', 
                detail          : '# 反余弦函数，三角函数\n' +
                                  '    float ACOS(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ASIN(close)',
                insertText      : 'ASIN(${1})', 
                detail          : '# 反正弦函数，三角函数\n' +
                                  '    float ASIN(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ATAN(close)',
                insertText      : 'ASIN(${1})', 
                detail          : '# 数字的反正切值，三角函数\n' +
                                  '    float ATAN(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CEIL(close)',
                insertText      : 'CEIL(${1})', 
                detail          : '# 向上取整数\n' +
                                  '    float CEIL(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'COS(close)',
                insertText      : 'COS(${1})', 
                detail          : '# 余弦函数，三角函数\n' +
                                  '    float COS(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'COSH(close)',
                insertText      : 'COSH(${1})', 
                detail          : '# 双曲正弦函数，三角函数\n' +
                                  '    float COSH(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'EXP(close)',
                insertText      : 'EXP(${1})', 
                detail          : '# 指数曲线，三角函数\n' +
                                  '    float EXP(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'FLOOR(close)',
                insertText      : 'FLOOR(${1})',
                detail          : '# 向下取整数\n' +
                                  '    float FLOOR(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LN(close)',
                insertText      : 'LN(${1})',
                detail          : '# 自然对数\n' +
                                  '    float LN(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LOG10(close)',
                insertText      : 'LOG10(${1})',
                detail          : '# 对数函数\n' +
                                  '    float LOG10(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SIN(close)',
                insertText      : 'SIN(${1})', 
                detail          : '# 正弦函数，三角函数\n' +
                                  '    float SIN(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SINH(close)',
                insertText      : 'SINH(${1})', 
                detail          : '# 双曲正弦函数，三角函数\n' +
                                  '    float SINH(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SQRT(close)',
                insertText      : 'SQRT(${1})', 
                detail          : '# 非负实数的平方根\n' +
                                  '    float SQRT(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TAN(close)',
                insertText      : 'TAN(${1})', 
                detail          : '# 正切函数，三角函数\n' +
                                  '    float TAN(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TANH(close)',
                insertText      : 'TANH(${1})', 
                detail          : '# 双曲正切函数，三角函数\n' +
                                  '    float TANH(close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ADX(high, low, close, timeperiod=14)',
                insertText      : 'ADX(${1})',
                detail          : '# 平均趋向指数\n' +
                                  '    float ADX(high, low, close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    使用ADX指标，指标判断盘整、振荡和单边趋势。\n' +
                                  '\n' +
                                  '公式：\n' +
                                  '    一、先决定股价趋势（Directional Movement，DM）是上涨或下跌：\n' +
                                  '    “所谓DM值，今日股价波动幅度大于昨日股价波动幅部分的最大值，可能是创高价的部分或创低价的部分；如果今日股价波动幅度较前一日小，则DM = 0。”\n' +
                                  '    若股价高点持续走高，为上涨趋势，记作 +DM。\n' +
                                  '    若为下跌趋势，记作 -DM。-DM的负号（–）是表示反向趋势（下跌），并非数值为负数。\n' +
                                  '    其他状况：DM = 0。\n' +
                                  '    二、寻找股价的真实波幅（True Range，TR）：\n' +
                                  '    所谓真实波幅（TR）是以最高价，最低价，及前一日收盘价三个价格做比较，求出当日股价波动的最大幅度。\n' +
                                  '    三、趋势方向需经由一段时间来观察，研判上才有意义。一般以14天为指标的观察周期：\n' +
                                  '    先计算出 +DM、–DM及TR的14日算术平均数，得到 +DM14、–DM14及TR14三组数据作为起始值，再计算各自的移动平均值（EMA）。\n' +
                                  '        +DI14 = +DM/TR14*100\n' +
                                  '        -DI14 = +DM/TR14*100\n' +
                                  '         DX = |(+DI14)-(-DI14)| / |(+DI14)+(-DI14)|\n' +
                                  '         DX运算结果取其绝对值，再将DX作移动平均，得到ADX\n' +
                                  '\n' +
                                  '特点：\n' +
                                  '    ADX无法告诉你趋势的发展方向。\n' +
                                  '    如果趋势存在，ADX可以衡量趋势的强度。不论上升趋势或下降趋势，ADX看起来都一样。\n' +
                                  '    ADX的读数越大，趋势越明显。衡量趋势强度时，需要比较几天的ADX 读数，观察ADX究竟是上升或下降。ADX读数上升，代表趋势转强；如果ADX读数下降，意味着趋势转弱。\n' +
                                  '    当ADX曲线向上攀升，趋势越来越强，应该会持续发展。如果ADX曲线下滑，代表趋势开始转弱，反转的可能性增加。\n' +
                                  '    单就ADX本身来说，由于指标落后价格走势，所以算不上是很好的指标，不适合单就ADX进行操作。可是，如果与其他指标配合运用，ADX可以确认市场是否存在趋势，并衡量趋势的强度。\n' +
                                  '\n' +
                                  '应用：\n' +
                                  '    +DI与–DI表示多空相反的二个动向，当据此绘出的两条曲线彼此纠结相缠时，代表上涨力道与下跌力道相当，多空势均力敌。当 +DI与–DI彼此穿越时，由下往上的一方其力道开始压过由上往下的另一方，此时出现买卖讯号。\n' +
                                  '    ADX可作为趋势行情的判断依据，当行情明显朝多空任一方向进行时，ADX数值都会显著上升，趋势走强。若行情呈现盘整格局时，ADX会低于 +DI与–DI二条线。若ADX数值低于20，则不论DI表现如何，均显示市场没有明显趋势。\n' +
                                  '    ADX持续偏高时，代表“超买”（Overbought）或“超卖”（Oversold）的现象，行情反转的机会将增加，此时则不适宜顺势操作。当ADX数值从上升趋势转为下跌时，则代表行情即将反转；若ADX数值由下跌趋势转为上升时，行情将止跌回升。\n' +
                                  '    总言之，DMI指标包含4条线：+DI、-DI、ADX和ADXR。+DI代表买盘的强度、-DI代表卖盘的强度；ADX代表趋势的强度、ADXR则为ADX的移动平均。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ADXR(high, low, close, timeperiod=14)',
                insertText      : 'ADXR(${1})',
                detail          : '# 平均趋向指数的趋向指数，判断ADX趋势\n' +
                                  '    float ADXR(high, low, close, timeperiod=14)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'APO(close, fastperiod=12, slowperiod=26, matype=0)',
                insertText      : 'APO(${1})',
                detail          : '# 绝对价格震荡指标\n' +
                                  '    float APO(close, fastperiod=12, slowperiod=26, matype=0)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'AROON(high, low, timeperiod=14)',
                insertText      : 'AROON(${1})',
                detail          : '# 阿隆指标\n' +
                                  '    aroondown, aroonup = AROON(high, low, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    \n' +
                                  '    该指标是通过计算自价格达到近期最高值和最低值以来所经过的期间数，阿隆指标帮助你预测价格趋势到趋势区域（或者反过来，从趋势区域到趋势）的变化。\n' +
                                  '\n' +
                                  '公式：\n' +
                                  '    \n' +
                                  '    Aroon(上升)=[(计算期天数-最高价后的天数)/计算期天数]*100\n' +
                                  '    Aroon(下降)=[(计算期天数-最低价后的天数)/计算期天数]*100\n' +
                                  '\n' +
                                  '应用：\n' +
                                  '    1. 极值0和100\n' +
                                  '    当UP线达到100时，市场处于强势；如果维持在70~100之间，表示一个上升趋势。同样，如果Down线达到0，表示处于弱势，如果维持在0~30之间，表示处于下跌趋势。如果两条线同处于极值水平，则表明一个更强的趋势。\n' +
                                  '    2. 平行运动\n' +
                                  '    如果两条线平行运动时，表明市场趋势被打破。可以预期该状况将持续下去，只到由极值水平或交叉穿行西安市出方向性运动为止。\n' +
                                  '    3. 交叉穿行\n' +
                                  '    当下行线上穿上行线时，表明潜在弱势，预期价格开始趋于下跌。反之，表明潜在强势，预期价格趋于走高。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'AROONOSC(high, low, timeperiod=14)',
                insertText      : 'AROONOSC(${1})',
                detail          : '# 阿隆振荡\n' +
                                  '    float AROONOSC(high, low, timeperiod=14)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BOP(open, high, low, close)',
                insertText      : 'BOP(${1})',
                detail          : '# 均势指标\n' +
                                  '    float BOP(open, high, low, close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CCI(high, low, close, timeperiod=14)',
                insertText      : 'CCI(${1})',
                detail          : '# 顺势指标\n' +
                                  '    float CCI(high, low, close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    CCI指标专门测量股价是否已超出常态分布范围\n' +
                                  '\n' +
                                  '应用：\n' +
                                  '    1. 当CCI指标曲线在+100线～-100线的常态区间里运行时,CCI指标参考意义不大，可以用KDJ等其它技术指标进行研判。\n' +
                                  '    2. 当CCI指标曲线从上向下突破+100线而重新进入常态区间时，表明市场价格的上涨阶段可能结束，将进入一个比较长时间的震荡整理阶段，应及时平多做空。\n' +
                                  '    3. 当CCI指标曲线从上向下突破-100线而进入另一个非常态区间（超卖区）时，表明市场价格的弱势状态已经形成，将进入一个比较长的寻底过程，可以持有空单等待更高利润。如果CCI指标曲线在超卖区运行了相当长的一段时间后开始掉头向上，表明价格的短期底部初步探明，可以少量建仓。CCI指标曲线在超卖区运行的时间越长，确认短期的底部的准确度越高。\n' +
                                  '    4. CCI指标曲线从下向上突破-100线而重新进入常态区间时，表明市场价格的探底阶段可能结束，有可能进入一个盘整阶段，可以逢低少量做多。\n' +
                                  '    5. CCI指标曲线从下向上突破+100线而进入非常态区间(超买区)时，表明市场价格已经脱离常态而进入强势状态，如果伴随较大的市场交投，应及时介入成功率将很大。\n' +
                                  '    6. CCI指标曲线从下向上突破+100线而进入非常态区间(超买区)后，只要CCI指标曲线一直朝上运行，表明价格依然保持强势可以继续持有待涨。但是，如果在远离+100线的地方开始掉头向下时，则表明市场价格的强势状态将可能难以维持，涨势可能转弱，应考虑卖出。如果前期的短期涨幅过高同时价格回落时交投活跃，则应该果断逢高卖出或做空。\n' +
                                  '    7. CCI主要是在超买和超卖区域发生作用，对急涨急跌的行情检测性相对准确。非常适用于股票、外汇、贵金属等市场的短期操作。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CMO(close, timeperiod=14)',
                insertText      : 'CMO(${1})',
                detail          : '# 钱德动量摆动指标\n' +
                                  '    float CMO(close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    与其他动量指标摆动指标如相对强弱指标（RSI）和随机指标（KDJ）不同，钱德动量指标在计算公式的分子中采用上涨日和下跌日的数据。\n' +
                                  '\n' +
                                  '公式：\n' +
                                  '    CMO=（Su－Sd）*100/（Su+Sd）\n' +
                                  '    其中：Su是今日收盘价与昨日收盘价（上涨日）差值加总。若当日下跌，则增加值为0；Sd是今日收盘价与做日收盘价（下跌日）差值的绝对值加总。若当日上涨，则增加值为0；指标应用:\n' +
                                  '    本指标类似RSI指标。\n' +
                                  '    当本指标下穿-50水平时是买入信号，上穿+50水平是卖出信号。\n' +
                                  '    钱德动量摆动指标的取值介于-100和100之间。\n' +
                                  '    本指标也能给出良好的背离信号。\n' +
                                  '    当股票价格创出新低而本指标未能创出新低时，出现牛市背离；    当股票价格创出新高而本指标未能创出新高时，当出现熊市背离时。\n' +
                                  '    我们可以用移动均值对该指标进行平滑。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'DX(high, low, close, timeperiod=14)',
                insertText      : 'DX(${1})',
                detail          : '# 动向指标或趋向指标\n' +
                                  '    float DX(high, low, close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    通过分析股票价格在涨跌过程中买卖双方力量均衡点的变化情况，即多空双方的力量的变化受价格波动的影响而发生由均衡到失衡的循环过程，从而提供对趋势判断依据的一种技术指标',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)',
                insertText      : 'MACD(${1})',
                detail          : '# 平滑异同移动平均线\n' +
                                  '    macd, macdsignal, macdhist = MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    利用收盘价的短期（常用为12日）指数移动平均线与长期（常用为26日）指数移动平均线之间的聚合与分离状况，对买进、卖出时机作出研判的技术指标。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MACDEXT(close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, ignalperiod=9, signalmatype=0)',
                insertText      : 'MACDEXT(${1})',
                detail          : '# 平滑异同移动平均线, 可指定MA类型\n' +
                                  '    macd, macdsignal, macdhist = MACDEXT(close, fastperiod=12, fastmatype=0, slowperiod=26, slowmatype=0, ignalperiod=9, signalmatype=0)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MACDFIX(close, signalperiod=9)',
                insertText      : 'MACDFIX(${1})',
                detail          : '# 移动平均趋同/趋同修正\n' +
                                  '    macd, macdsignal, macdhist = MACDFIX(close, signalperiod=9)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MFI(high, low, close, volume, timeperiod=14)',
                insertText      : 'MFI(${1})',
                detail          : '# 资金流量指标 \n' +
                                  '    float MFI(high, low, close, volume, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    属于量价类指标，反映市场的运行趋势',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MINUS_DI(high, low, close, timeperiod=14)',
                insertText      : 'DMI(${1})', 
                detail          : '# 下升动向值\n' +
                                  '    float MINUS_DI(high, low, close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    通过分析股票价格在涨跌过程中买卖双方力量均衡点的变化情况，即多空双方的力量的变化受价格波动的影响而发生由均衡到失衡的循环过程，从而提供对趋势判断依据的一种技术指标',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MINUS_DM(high, low, timeperiod=14)',
                insertText      : 'MINUS_DM(${1})',
                detail          : '# 上升动向值 DMI中的DM代表正趋向变动值即上升动向值\n' +
                                  '    float MINUS_DM(high, low, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    通过分析股票价格在涨跌过程中买卖双方力量均衡点的变化情况，即多空双方的力量的变化受价格波动的影响而发生由均衡到失衡的循环过程，从而提供对趋势判断依据的一种技术指标',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MOM(close, timeperiod=10)',
                insertText      : 'MOM(${1})',
                detail          : '# 上升动向值\n' +
                                  '    float MOM(close, timeperiod=10)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    投资学中意思为续航，指股票(或经济指数)持续增长的能力。研究发现，赢家组合在牛市中存在着正的动量效应，输家组合在熊市中存在着负的动量效应',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PLUS_DI(high, low, close, timeperiod=14)',
                insertText      : 'PLUS_DI(${1})',
                detail          : '# 加方向指数\n' +
                                  '    float PLUS_DI(high, low, close, timeperiod=14)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PLUS_DM(high, low, timeperiod=14)',
                insertText      : 'PLUS_DM(${1})',
                detail          : '# 加方移动\n' +
                                  '    float PLUS_DM(high, low, timeperiod=14)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'PPO(close, fastperiod=12, slowperiod=26, matype=0)',
                insertText      : 'PPO(${1})',
                detail          : '# 价格震荡百分比指数\n' +
                                  '    float PPO(close, fastperiod=12, slowperiod=26, matype=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    价格震荡百分比指标（PPO）是一个和MACD指标非常接近的指标。\n' +
                                  '    PPO标准设定和MACD设定非常相似：12,26,9和PPO，和MACD一样说明了两条移动平均线的差距，但是它们有一个差别是PPO是用百分比说明',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ROC(close, timeperiod=10)',
                insertText      : 'ROC(${1})',
                detail          : '# 变动率指标\n' +
                                  '    float ROC(close, timeperiod=10)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    ROC是由当天的股价与一定的天数之前的某一天股价比较，其变动速度的大小,来反映股票市变动的快慢程度',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ROCP(close, timeperiod=10)',
                insertText      : 'ROCP(${1})',
                detail          : '# 涨幅\n' +
                                  '    float ROCP(close, timeperiod=10)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ROCR(close, timeperiod=10)',
                insertText      : 'ROCR(${1})',
                detail          : '# 波幅\n' +
                                  '    float ROCR(close, timeperiod=10)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ROCR100(close, timeperiod=10)',
                insertText      : 'ROCR100(${1})',
                detail          : '# 波幅百分比\n' +
                                  '    float ROCR100(close, timeperiod=10)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'RSI(close, timeperiod=14)',
                insertText      : 'RSI(${1})',
                detail          : '# 相对强弱指数  \n' +
                                  '    float RSI(close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    是通过比较一段时期内的平均收盘涨数和平均收盘跌数来分析市场买沽盘的意向和实力，从而作出未来市场的走势。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, lowd_matype=0)',
                insertText      : 'STOCH(${1})',
                detail          : '# 随机指标,俗称KD\n' +
                                  '    slowk, slowd = STOCH(high, low, close, fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, lowd_matype=0)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'STOCHF(high, low, close, fastk_period=5, fastd_period=3, fastd_matype=0)',
                insertText      : 'STOCHF(${1})',
                detail          : '# 快速随机\n'  +
                                  '    fastk, fastd = STOCHF(high, low, close, fastk_period=5, fastd_period=3, fastd_matype=0)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'STOCHRSI(close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)',
                insertText      : 'STOCHRSI(${1})',
                detail          : '# 随机相对强度指数\n'  +
                                  '    fastk, fastd = STOCHRSI(close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TRIX(close, timeperiod=30)',
                insertText      : 'TRIX(${1})',
                detail          : '# 三天平滑均线的变化率(ROC)\n' +
                                  '    float TRIX(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ULTOSC(high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28)',
                insertText      : 'ULTOSC(${1})',
                detail          : '# 终极波动指标   \n' +
                                  '    float ULTOSC(high, low, close, timeperiod1=7, timeperiod2=14, timeperiod3=28)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    UOS是一种多方位功能的指标，除了趋势确认及超买超卖方面的作用之外，它的“突破”讯号不仅可以提供最适当的交易时机之外，更可以进一步加强指标的可靠度。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'WILLR(high, low, close, timeperiod=14)',
                insertText      : 'WILLR(${1})',
                detail          : '# 威廉指标 \n' +
                                  '    float WILLR(high, low, close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    WMS表示的是市场处于超买还是超卖状态。股票投资分析方法主要有如下三种：基本分析、技术分析、演化分析。在实际应用中，它们既相互联系，又有重要区别。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)',
                insertText      : 'BBANDS(${1})',
                detail          : '# 布林线指标\n' +
                                  '    upperband, middleband, lowerband = BBANDS(close, timeperiod=5, nbdevup=2, nbdevdn=2, matype=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    其利用统计原理，求出股价的标准差及其信赖区间，从而确定股价的波动范围及未来走势，利用波带显示股价的安全高低价位，因而也被称为布林带。 ',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'DEMA(close, timeperiod=30)',
                insertText      : 'DEMA(${1})',
                detail          : '# 双移动平均线\n' +
                                  '    float DEMA(close, timeperiod=30)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    两条移动平均线来产生趋势信号，较长期者用来识别趋势，较短期者用来选择时机。正是两条平均线及价格三者的相互作用，才共同产生了趋势信号。 ',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'EMA(close, timeperiod=30)',
                insertText      : 'EMA(${1})',
                detail          : '# 指数平均数\n' +
                                  '    float EMA(close, timeperiod=30)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    是一种趋向类指标，其构造原理是仍然对价格收盘价进行算术平均，并根据计算结果来进行分析，用于判断价格未来走势的变动趋势。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'HT_TRENDLINE(close)',
                insertText      : 'HT_TRENDLINE(${1})',
                detail          : '# 希尔伯特瞬时变换\n' +
                                  '    float HT_TRENDLINE(close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    是一种趋向类指标，其构造原理是仍然对价格收盘价进行算术平均，并根据计算结果来进行分析，用于判断价格未来走势的变动趋势。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'KAMA(close, timeperiod=30)',
                insertText      : 'KAMA(${1})',
                detail          : '# 考夫曼的自适应移动平均线\n' +
                                  '    float KAMA(close, timeperiod=30)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    短期均线贴近价格走势，灵敏度高，但会有很多噪声，产生虚假信号；长期均线在判断趋势上一般比较准确, 但是长期均线有着严重滞后的问题。我们想得到这样的均线，当价格沿一个方向快速移动时，短期的移动平均线是最合适的；当价格在横盘的过程中，长期移动平均线是合适的。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MA(close, timeperiod=30, matype=0)',
                insertText      : 'MA(${1})',
                detail          : '# 移动平均线\n' +
                                  '    float MA(close, timeperiod=30, matype=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    移动平均线，Moving Average，简称MA，原本的意思是移动平均，由于我们将其制作成线形，所以一般称之为移动平均线，简称均线。它是将某一段时间的收盘价之和除以该周期。 比如日线MA5指5天内的收盘价除以5 ',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MAMA(close, fastlimit=0, slowlimit=0)',
                insertText      : 'MESA(${1})', 
                detail          : '# MESA自适应移动平均线\n' +
                                  '    mama, fama = MAMA(close, fastlimit=0, slowlimit=0)\n' ,
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MAVP(close, periods, minperiod=2, maxperiod=30, matype=0)',
                insertText      : 'MAVP(${1})', 
                detail          : '# 可变周期的移动平均线\n' +
                                  '    float MAVP(close, periods, minperiod=2, maxperiod=30, matype=0)\n' ,
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MIDPOINT(close, timeperiod=14)',
                insertText      : 'MIDPOINT(${1})', 
                detail          : '# 中间点位\n' +
                                  '    float MIDPOINT(close, timeperiod=14)\n' ,
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MIDPRICE(high, low, timeperiod=14)',
                insertText      : 'MIDPRICE(${1})', 
                detail          : '# 中间价\n' +
                                  '    float MIDPRICE(high, low, timeperiod=14)\n' ,
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SAR(high, low, acceleration=0, maximum=0)',
                insertText      : 'SAR(${1})',
                detail          : '# 抛物线指标\n' +
                                  '    float SAR(high, low, acceleration=0, maximum=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    抛物线转向也称停损点转向，是利用抛物线方式，随时调整停损点位置以观察买卖点。由于停损点（又称转向点SAR）以弧形的方式移动，故称之为抛物线转向指标',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SAREXT(high, low, startvalue=0, offsetonreverse=0, accelerationinitlong=0, accelerationlong=0, ccelerationmaxlong=0, accelerationinitshort=0, accelerationshort=0, accelerationmaxshort=0)',
                insertText      : 'SAREXT(${1})', 
                detail          : '# 抛物线指标扩展\n' +
                                  '    float SAREXT(high, low, startvalue=0, offsetonreverse=0, accelerationinitlong=0, accelerationlong=0, ccelerationmaxlong=0, accelerationinitshort=0, accelerationshort=0, accelerationmaxshort=0)\n' ,
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'SMA(close, timeperiod=30)',
                insertText      : 'SMA(${1})',
                detail          : '# 简单移动平均线\n' +
                                  '    float SMA(close, timeperiod=30)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    移动平均线，Moving Average，简称MA，原本的意思是移动平均，由于我们将其制作成线形，所以一般称之为移动平均线，简称均线。它是将某一段时间的收盘价之和除以该周期。 比如日线MA5指5天内的收盘价除以5 ',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'T3(close, timeperiod=5, vfactor=0)',
                insertText      : 'T3(${1})',
                detail          : '# 三重指数移动平均线\n' +
                                  '    float T3(close, timeperiod=5, vfactor=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    TRIX长线操作时采用本指标的讯号，长时间按照本指标讯号交易，获利百分比大于损失百分比，利润相当可观。 比如日线MA5指5天内的收盘价除以5 。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TEMA(close, timeperiod=30)',
                insertText      : 'TEMA(${1})', 
                detail          : '# 三重指数移动平均线\n' +
                                  '    float TEMA(close, timeperiod=30)\n' ,
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TRIMA(close, timeperiod=30)',
                insertText      : 'TRIMA(${1})', 
                detail          : '# 三角移动平均线\n' +
                                  '    float TRIMA(close, timeperiod=30)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'WMA(close, timeperiod=30)',
                insertText      : 'WMA(${1})',
                detail          : '# 加权移动平均线\n' +
                                  '    float WMA(close, timeperiod=30)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    移动加权平均法是指以每次进货的成本加上原有库存存货的成本，除以每次进货数量与原有库存存货的数量之和，据以计算加权平均单位成本，以此为基础计算当月发出存货的成本和期末存货的成本的一种方法',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDL2CROWS(open, high, low, close)',
                insertText      : 'CDL2CROWS(${1})',
                detail          : '# 两只乌鸦\n' +
                                  '    int CDL2CROWS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，第一天长阳，第二天高开收阴，第三天再次高开继续收阴，收盘比前一日收盘价低，预示股价下跌。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDL3BLACKCROWS(open, high, low, close)',
                insertText      : 'CDL3BLACKCROWS(${1})',
                detail          : '# 三只乌鸦\n' +
                                  '    int CDL3BLACKCROWS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，连续三根阴线，每日收盘价都下跌且接近最低价，每日开盘价都在上根K线实体内，预示股价下跌。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDL3INSIDE(open, high, low, close)',
                insertText      : 'CDL3INSIDE(${1})',
                detail          : '# 三内部上涨和下跌\n' +
                                  '    int CDL3INSIDE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，母子信号+长K线，以三内部上涨为例，K线为阴阳阳，第三天收盘价高于第一天开盘价，第二天K线在第一天K线内部，预示着股价上涨。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDL3LINESTRIKE(open, high, low, close)',
                insertText      : 'CDL3LINESTRIKE(${1})',
                detail          : '# 三线打击\n' +
                                  '    int CDL3LINESTRIKE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    四日K线模式，前三根阳线，每日收盘价都比前一日高，开盘价在前一日实体内，第四日市场高开，收盘价低于第一日开盘价，预示股价下跌。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDL3OUTSIDE(open, high, low, close)',
                insertText      : 'CDL3OUTSIDE(${1})',
                detail          : '# 三外部上涨和下跌\n' +
                                  '    int CDL3OUTSIDE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，与三内部上涨和下跌类似，K线为阴阳阳，但第一日与第二日的K线形态相反，以三外部上涨为例，第一日K线在第二日K线内部，预示着股价上涨。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDL3STARSINSOUTH(open, high, low, close)',
                insertText      : 'CDL3STARSINSOUTH(${1})',
                detail          : '# 南方三星\n' +
                                  '    int CDL3STARSINSOUTH(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，与大敌当前相反，三日K线皆阴，第一日有长下影线，第二日与第一日类似，K线整体小于第一日，第三日无下影线实体信号，成交价格都在第一日振幅之内，预示下跌趋势反转，股价上升。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDL3WHITESOLDIERS(open, high, low, close)',
                insertText      : 'CDL3WHITESOLDIERS(${1})',
                detail          : '# 三个白兵\n' +
                                  '    int CDL3WHITESOLDIERS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，三日K线皆阳，每日收盘价变高且接近最高价，开盘价在前一日实体上半部，预示股价上升。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLABANDONEDBABY(open, high, low, close, penetration=0)',
                insertText      : 'CDLABANDONEDBABY(${1})',
                detail          : '# 弃婴\n' +
                                  '    int CDLABANDONEDBABY(open, high, low, close, penetration=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，第二日价格跳空且收十字星（开盘价与收盘价接近，最高价最低价相差不大），预示趋势反转，发生在顶部下跌，底部上涨。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLADVANCEBLOCK(open, high, low, close)',
                insertText      : 'CDLADVANCEBLOCK(${1})',
                detail          : '# 大敌当前\n' +
                                  '    int CDLADVANCEBLOCK(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，三日都收阳，每日收盘价都比前一日高，开盘价都在前一日实体以内，实体变短，上影线变长。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLBELTHOLD(open, high, low, close)',
                insertText      : 'CDLBELTHOLD(${1})',
                detail          : '# 捉腰带线\n' +
                                  '    int CDLBELTHOLD(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    两日K线模式，下跌趋势中，第一日阴线，第二日开盘价为最低价，阳线，收盘价接近最高价，预示价格上涨。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLBREAKAWAY(open, high, low, close)',
                insertText      : 'CDLBREAKAWAY(${1})',
                detail          : '# 脱离\n' +
                                  '    int CDLBREAKAWAY(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    五日K线模式，以看涨脱离为例，下跌趋势中，第一日长阴线，第二日跳空阴线，延续趋势开始震荡，第五日长阳线，收盘价在第一天收盘价与第二天开盘价之间，预示价格上涨。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLCLOSINGMARUBOZU(open, high, low, close)',
                insertText      : 'CDLCLOSINGMARUBOZU(${1})',
                detail          : '# 收盘缺影线\n' +
                                  '    int CDLCLOSINGMARUBOZU(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，以阳线为例，最低价低于开盘价，收盘价等于最高价，预示着趋势持续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLCONCEALBABYSWALL(open, high, low, close)',
                insertText      : 'CDLCONCEALBABYSWALL(${1})',
                detail          : '# 藏婴吞没\n' +
                                  '    int CDLCONCEALBABYSWALL(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    四日K线模式，下跌趋势中，前两日阴线无影线，第二日开盘、收盘价皆低于第二日，第三日倒锤头，第四日开盘价高于前一日最高价，收盘价低于前一日最低价，预示着底部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLCOUNTERATTACK(open, high, low, close)',
                insertText      : 'CDLCOUNTERATTACK(${1})',
                detail          : '# 反击线\n' +
                                  '    int CDLCOUNTERATTACK(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，与分离线类似。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLDARKCLOUDCOVER(open, high, low, close, penetration=0)',
                insertText      : 'CDLDARKCLOUDCOVER(${1})',
                detail          : '# 乌云压顶\n' +
                                  '    int CDLDARKCLOUDCOVER(open, high, low, close, penetration=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，第一日长阳，第二日开盘价高于前一日最高价，收盘价处于前一日实体中部以下，预示着股价下跌。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLDOJI(open, high, low, close)',
                insertText      : 'CDLDOJI(${1})',
                detail          : '# 十字\n' +
                                  '    int CDLDOJI(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，开盘价与收盘价基本相同。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLDOJISTAR(open, high, low, close)',
                insertText      : 'CDLDOJISTAR(${1})',
                detail          : '# 十字星\n' +
                                  '    int CDLDOJISTAR(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，开盘价与收盘价基本相同，上下影线不会很长，预示着当前趋势反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLDRAGONFLYDOJI(open, high, low, close)',
                insertText      : 'CDLDRAGONFLYDOJI(${1})',
                detail          : '# 蜻蜓十字/T形十字\n' +
                                  '    int CDLDRAGONFLYDOJI(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，开盘后价格一路走低，之后收复，收盘价与开盘价相同，预示趋势反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLENGULFING(open, high, low, close)',
                insertText      : 'CDLENGULFING(${1})',
                detail          : '# 吞噬模式\n' +
                                  '    int CDLENGULFING(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    两日K线模式，分多头吞噬和空头吞噬，以多头吞噬为例，第一日为阴线，第二日阳线，第一日的开盘价和收盘价在第二日开盘价收盘价之内，但不能完全相同。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLEVENINGDOJISTAR(open, high, low, close, penetration=0)',
                insertText      : 'CDLEVENINGDOJISTAR(${1})',
                detail          : '# 十字暮星\n' +
                                  '    int CDLEVENINGDOJISTAR(open, high, low, close, penetration=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，基本模式为暮星，第二日收盘价和开盘价相同，预示顶部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLEVENINGSTAR(open, high, low, close, penetration=0)',
                insertText      : 'CDLEVENINGSTAR(${1})',
                detail          : '# 暮星\n' +
                                  '    int CDLEVENINGSTAR(open, high, low, close, penetration=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，与晨星相反，上升趋势中, 第一日阳线，第二日价格振幅较小，第三日阴线，预示顶部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLGAPSIDESIDEWHITE(open, high, low, close)',
                insertText      : 'CDLGAPSIDESIDEWHITE(${1})',
                detail          : '# 上/下跳空并列阳线\n' +
                                  '    int CDLGAPSIDESIDEWHITE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，上升趋势向上跳空，下跌趋势向下跳空, 第一日与第二日有相同开盘价，实体长度差不多，则趋势持续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLGRAVESTONEDOJI(open, high, low, close)',
                insertText      : 'CDLGRAVESTONEDOJI(${1})',
                detail          : '# 墓碑十字/倒T十字\n' +
                                  '    int CDLGRAVESTONEDOJI(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，开盘价与收盘价相同，上影线长，无下影线，预示底部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHAMMER(open, high, low, close)',
                insertText      : 'CDLHAMMER(${1})',
                detail          : '# 锤头\n' +
                                  '    int CDLHAMMER(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，实体较短，无上影线，下影线大于实体长度两倍，处于下跌趋势底部，预示反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHANGINGMAN(open, high, low, close)',
                insertText      : 'CDLHANGINGMAN(${1})',
                detail          : '# 上吊线\n' +
                                  '    int CDLHANGINGMAN(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，形状与锤子类似，处于上升趋势的顶部，预示着趋势反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHARAMI(open, high, low, close)',
                insertText      : 'CDLHARAMI(${1})',
                detail          : '# 母子线\n' +
                                  '    int CDLHARAMI(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，分多头母子与空头母子，两者相反，以多头母子为例，在下跌趋势中，第一日K线长阴，第二日开盘价收盘价在第一日价格振幅之内，为阳线，预示趋势反转，股价上升。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHARAMICROSS(open, high, low, close)',
                insertText      : 'CDLHARAMICROSS(${1})',
                detail          : '# 十字孕线\n' +
                                  '    int CDLHARAMICROSS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，与母子县类似，若第二日K线是十字线，便称为十字孕线，预示着趋势反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHIGHWAVE(open, high, low, close)',
                insertText      : 'CDLHIGHWAVE(${1})',
                detail          : '# 风高浪大线\n' +
                                  '    int CDLHIGHWAVE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，具有极长的上/下影线与短的实体，预示着趋势反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHIKKAKE(open, high, low, close)',
                insertText      : 'CDLHIKKAKE(${1})',
                detail          : '# 陷阱\n' +
                                  '    int CDLHIKKAKE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，与母子类似，第二日价格在前一日实体范围内, 第三日收盘价高于前两日，反转失败，趋势继续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHIKKAKEMOD(open, high, low, close)',
                insertText      : 'CDLHIKKAKEMOD(${1})',
                detail          : '# 修正陷阱\n' +
                                  '    int CDLHIKKAKEMOD(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，与陷阱类似，上升趋势中，第三日跳空高开；下跌趋势中，第三日跳空低开，反转失败，趋势继续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLHOMINGPIGEON(open, high, low, close)',
                insertText      : 'CDLHOMINGPIGEON(${1})',
                detail          : '# 家鸽\n' +
                                  '    int CDLHOMINGPIGEON(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，与母子线类似，不同的的是二日K线颜色相同，第二日最高价、最低价都在第一日实体之内，预示着趋势反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLIDENTICAL3CROWS(open, high, low, close)',
                insertText      : 'CDLIDENTICAL3CROWS(${1})',
                detail          : '# 三胞胎乌鸦\n' +
                                  '    int CDLIDENTICAL3CROWS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，上涨趋势中，三日都为阴线，长度大致相等，每日开盘价等于前一日收盘价，收盘价接近当日最低价，预示价格下跌。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLINNECK(open, high, low, close)',
                insertText      : 'CDLINNECK(${1})',
                detail          : '# 颈内线\n' +
                                  '    int CDLINNECK(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，下跌趋势中，第一日长阴线，第二日开盘价较低，收盘价略高于第一日收盘价，阳线，实体较短，预示着下跌继续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLINVERTEDHAMMER(open, high, low, close)',
                insertText      : 'CDLINVERTEDHAMMER(${1})',
                detail          : '# 倒锤头\n' +
                                  '    int CDLINVERTEDHAMMER(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，上影线较长，长度为实体2倍以上，无下影线，在下跌趋势底部，预示着趋势反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLKICKING(open, high, low, close)',
                insertText      : 'CDLKICKING(${1})',
                detail          : '# 反冲形态\n' +
                                  '    int CDLKICKING(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，与分离线类似，两日K线为秃线，颜色相反，存在跳空缺口。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLKICKINGBYLENGTH(open, high, low, close)',
                insertText      : 'CDLKICKINGBYLENGTH(${1})',
                detail          : '# 由较长缺影线决定的反冲形态\n' +
                                  '    int CDLKICKINGBYLENGTH(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，与反冲形态类似，较长缺影线决定价格的涨跌。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLLADDERBOTTOM(open, high, low, close)',
                insertText      : 'CDLLADDERBOTTOM(${1})',
                detail          : '# 梯底\n' +
                                  '    int CDLLADDERBOTTOM(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    五日K线模式，下跌趋势中，前三日阴线，开盘价与收盘价皆低于前一日开盘、收盘价，第四日倒锤头，第五日开盘价高于前一日开盘价，阳线，收盘价高于前几日价格振幅，预示着底部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLLONGLEGGEDDOJI(open, high, low, close)',
                insertText      : 'CDLLONGLEGGEDDOJI(${1})',
                detail          : '# 长脚十字\n' +
                                  '    int CDLLONGLEGGEDDOJI(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，开盘价与收盘价相同居当日价格中部，上下影线长，表达市场不确定性。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLLONGLINE(open, high, low, close)',
                insertText      : 'CDLLONGLINE(${1})',
                detail          : '# 长蜡烛\n' +
                                  '    int CDLLONGLINE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，K线实体长，无上下影线。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLMARUBOZU(open, high, low, close)',
                insertText      : 'CDLMARUBOZU(${1})',
                detail          : '# 光头光脚/缺影线\n' +
                                  '    int CDLMARUBOZU(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，上下两头都没有影线的实体，阴线预示着熊市持续或者牛市反转，阳线相反。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLMATCHINGLOW(open, high, low, close)',
                insertText      : 'CDLMATCHINGLOW(${1})',
                detail          : '# 相同低价\n' +
                                  '    int CDLMATCHINGLOW(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，下跌趋势中，第一日长阴线，第二日阴线，收盘价与前一日相同，预示底部确认，该价格为支撑位。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLMATHOLD(open, high, low, close, penetration=0)',
                insertText      : 'CDLMATHOLD(${1})',
                detail          : '# 铺垫\n' +
                                  '    int CDLMATHOLD(open, high, low, close, penetration=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    五日K线模式，上涨趋势中，第一日阳线，第二日跳空高开影线，第三、四日短实体影线，第五日阳线，收盘价高于前四日，预示趋势持续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLMORNINGDOJISTAR(open, high, low, close, penetration=0)',
                insertText      : 'CDLMORNINGDOJISTAR(${1})',
                detail          : '# 十字晨星\n' +
                                  '    int CDLMORNINGDOJISTAR(open, high, low, close, penetration=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，基本模式为晨星，第二日K线为十字星，预示底部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLMORNINGSTAR(open, high, low, close, penetration=0)',
                insertText      : 'CDLMORNINGSTAR(${1})',
                detail          : '# 晨星\n' +
                                  '    int CDLMORNINGSTAR(open, high, low, close, penetration=0)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，下跌趋势，第一日阴线，第二日价格振幅较小，第三天阳线，预示底部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLONNECK(open, high, low, close)',
                insertText      : 'CDLONNECK(${1})',
                detail          : '# 颈上线\n' +
                                  '    int CDLONNECK(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，下跌趋势中，第一日长阴线，第二日开盘价较低，收盘价与前一日最低价相同，阳线，实体较短，预示着延续下跌趋势。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLPIERCING(open, high, low, close)',
                insertText      : 'CDLPIERCING(${1})',
                detail          : '# 刺透形态\n' +
                                  '    int CDLPIERCING(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    两日K线模式，下跌趋势中，第一日阴线，第二日收盘价低于前一日最低价，收盘价处在第一日实体上部，预示着底部反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLRICKSHAWMAN(open, high, low, close)',
                insertText      : 'CDLRICKSHAWMAN(${1})',
                detail          : '# 黄包车夫\n' +
                                  '    int CDLRICKSHAWMAN(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，与长腿十字线类似，若实体正好处于价格振幅中点，称为黄包车夫。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLRISEFALL3METHODS(open, high, low, close)',
                insertText      : 'CDLRISEFALL3METHODS(${1})',
                detail          : '# 上升/下降三法\n' +
                                  '    int CDLRISEFALL3METHODS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '     五日K线模式，以上升三法为例，上涨趋势中，第一日长阳线，中间三日价格在第一日范围内小幅震荡，第五日长阳线，收盘价高于第一日收盘价，预示股价上升。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLSEPARATINGLINES(open, high, low, close)',
                insertText      : 'CDLSEPARATINGLINES(${1})',
                detail          : '# 分离线\n' +
                                  '    int CDLSEPARATINGLINES(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，上涨趋势中，第一日阴线，第二日阳线，第二日开盘价与第一日相同且为最低价，预示着趋势继续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLSHOOTINGSTAR(open, high, low, close)',
                insertText      : 'CDLSHOOTINGSTAR(${1})',
                detail          : '# 射击之星\n' +
                                  '    int CDLSHOOTINGSTAR(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，上影线至少为实体长度两倍，没有下影线，预示着股价下跌',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLSHORTLINE(open, high, low, close)',
                insertText      : 'CDLSHORTLINE(${1})',
                detail          : '# 短蜡烛\n' +
                                  '    int CDLSHORTLINE(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，实体短，无上下影线',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLSPINNINGTOP(open, high, low, close)',
                insertText      : 'CDLSPINNINGTOP(${1})',
                detail          : '# 纺锤\n' +
                                  '    int CDLSPINNINGTOP(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线，实体小。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLSTALLEDPATTERN(open, high, low, close)',
                insertText      : 'CDLSTALLEDPATTERN(${1})',
                detail          : '# 停顿形态\n' +
                                  '    int CDLSTALLEDPATTERN(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，上涨趋势中，第二日长阳线，第三日开盘于前一日收盘价附近，短阳线，预示着上涨结束',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLSTICKSANDWICH(open, high, low, close)',
                insertText      : 'CDLSTICKSANDWICH(${1})',
                detail          : '# 条形三明治\n' +
                                  '    int CDLSTICKSANDWICH(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，第一日长阴线，第二日阳线，开盘价高于前一日收盘价，第三日开盘价高于前两日最高价，收盘价于第一日收盘价相同。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLTAKURI(open, high, low, close)',
                insertText      : 'CDLTAKURI(${1})',
                detail          : '# 探水竿\n' +
                                  '    int CDLTAKURI(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一日K线模式，大致与蜻蜓十字相同，下影线长度长。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLTASUKIGAP(open, high, low, close)',
                insertText      : 'CDLTASUKIGAP(${1})',
                detail          : '# 跳空并列阴阳线\n' +
                                  '    int CDLTASUKIGAP(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，分上涨和下跌，以上升为例，前两日阳线，第二日跳空，第三日阴线，收盘价于缺口中，上升趋势持续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLTHRUSTING(open, high, low, close)',
                insertText      : 'CDLTHRUSTING(${1})',
                detail          : '# 插入\n' +
                                  '    int CDLTHRUSTING(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    二日K线模式，与颈上线类似，下跌趋势中，第一日长阴线，第二日开盘价跳空，收盘价略低于前一日实体中部，与颈上线相比实体较长，预示着趋势持续。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLTRISTAR(open, high, low, close)',
                insertText      : 'CDLTRISTAR(${1})',
                detail          : '# 三星\n' +
                                  '    int CDLTRISTAR(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，由三个十字组成，第二日十字必须高于或者低于第一日和第三日，预示着反转。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLUNIQUE3RIVER(open, high, low, close)',
                insertText      : 'CDLUNIQUE3RIVER(${1})',
                detail          : '# 奇特三河床\n' +
                                  '    int CDLUNIQUE3RIVER(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，下跌趋势中，第一日长阴线，第二日为锤头，最低价创新低，第三日开盘价低于第二日收盘价，收阳线，收盘价不高于第二日收盘价，预示着反转，第二日下影线越长可能性越大。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLUPSIDEGAP2CROWS(open, high, low, close)',
                insertText      : 'CDLUPSIDEGAP2CROWS(${1})',
                detail          : '# 向上跳空的两只乌鸦\n' +
                                  '    int CDLUPSIDEGAP2CROWS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    三日K线模式，第一日阳线，第二日跳空以高于第一日最高价开盘，收阴线，第三日开盘价高于第二日，收阴线，与第一日比仍有缺口。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CDLXSIDEGAP3METHODS(open, high, low, close)',
                insertText      : 'CDLXSIDEGAP3METHODS(${1})',
                detail          : '# 上升/下降跳空三法\n' +
                                  '    int CDLXSIDEGAP3METHODS(open, high, low, close)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    五日K线模式，以上升跳空三法为例，上涨趋势中，第一日长阳线，第二日短阳线，第三日跳空阳线，第四日阴线，开盘价与收盘价于前两日实体内，第五日长阳线，收盘价高于第一日收盘价，预示股价上升。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'AVGPRICE(open, high, low, close)',
                insertText      : 'AVGPRICE(${1})',
                detail          : '# 平均价格函数\n' +
                                  '    float AVGPRICE(open, high, low, close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'MEDPRICE(high, low)',
                insertText      : 'MEDPRICE(${1})',
                detail          : '# 中位数价格\n' +
                                  '    float MEDPRICE(high, low)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TYPPRICE(high, low, close)',
                insertText      : 'TYPPRICE(${1})',
                detail          : '# 代表性价格\n' +
                                  '    float TYPPRICE(high, low, close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'WCLPRICE(high, low, close)',
                insertText      : 'WCLPRICE(${1})',
                detail          : '# 加权收盘价\n' +
                                  '    float WCLPRICE(high, low, close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'BETA(high, low, timeperiod=5)',
                insertText      : 'BETA(${1})',
                detail          : '# β系数也称为贝塔系数\n' +
                                  '    float BETA(high, low, timeperiod=5)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一种风险指数，用来衡量个别股票或股票基金相对于整个股市的价格波动情况\n' +
                                  '    贝塔系数衡量股票收益相对于业绩评价基准收益的总体波动性，是一个相对指标。 β 越高，意味着股票相对于业绩评价基准的波动性越大。 β 大于 1 ，    则股票的波动性大于业绩评价基准的波动性。反之亦然。\n' +
                                  '用途：\n' +
                                  '    1）计算资本成本，做出投资决策（只有回报率高于资本成本的项目才应投资）；    2）计算资本成本，制定业绩考核及激励标准；    3）计算资本成本，进行资产估值（Beta是现金流贴现模型的基础）；    4）确定单个资产或组合的系统风险，用于资产组合的投资管理，特别是股指期货或其他金融衍生品的避险（或投机）',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'CORREL(high, low, timeperiod=30)',
                insertText      : 'CORREL(${1})',
                detail          : '# 皮尔逊相关系数\n' +
                                  '    float CORREL(high, low, timeperiod=30)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    用于度量两个变量X和Y之间的相关（线性相关），其值介于-1与1之间\n' +
                                  '    皮尔逊相关系数是一种度量两个变量间相关程度的方法。它是一个介于 1 和 -1 之间的值，    其中，1 表示变量完全正相关， 0 表示无关，-1 表示完全负相关。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LINEARREG(close, timeperiod=14)',
                insertText      : 'LINEARREG(${1})',
                detail          : '# 线性回归\n' +
                                  '    float LINEARREG(close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    来确定两种或两种以上变量间相互依赖的定量关系的一种统计分析方法\n' +
                                  '    其表达形式为y = w\'x+e，e为误差服从均值为0的正态分布。\n' +
                                  '    直线回归方程：当两个变量x与y之间达到显著地线性相关关系时,应用最小二乘法原理确定一条最优直线的直线方程y=a+bx,这条回归直线与个相关点的距离比任何其他直线与相关点的距离都小,是最佳的理想直线.\n' +
                                  '    回归截距a：表示直线在y轴上的截距,代表直线的起点.\n' +
                                  '    回归系数b：表示直线的斜率,他的实际意义是说明x每变化一个单位时,影响y平均变动的数量.\n' +
                                  '    即x每增加1单位,y变化b个单位',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LINEARREG_ANGLE(close, timeperiod=14)',
                insertText      : 'LINEARREG_ANGLE(${1})',
                detail          : '# 线性回归的角度\n' +
                                  '    float LINEARREG_ANGLE(close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    来确定价格的角度变化。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LINEARREG_INTERCEPT(close, timeperiod=14)',
                insertText      : 'LINEARREG_INTERCEPT(${1})',
                detail          : '# 线性回归截距\n' +
                                  '    float LINEARREG_INTERCEPT(close, timeperiod=14)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'LINEARREG_SLOPE(close, timeperiod=14)',
                insertText      : 'LINEARREG_SLOPE(${1})',
                detail          : '# 线性回归斜率指标\n' +
                                  '    float LINEARREG_SLOPE(close, timeperiod=14)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'STDDEV(close, timeperiod=5, nbdev=1)',
                insertText      : 'STDDEV(${1})',
                detail          : '# 标准偏差\n' +
                                  '    float STDDEV(close, timeperiod=5, nbdev=1)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    种量度数据分布的分散程度之标准，用以衡量数据值偏离算术平均值的程度。标准偏差越小，这些值偏离平均值就越少，反之亦然。标准偏差的大小可通过标准偏差与平均值的倍率关系来衡量',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TSF(close, timeperiod=14)',
                insertText      : 'TSF(${1})',
                detail          : '# 时间序列预测\n' +
                                  '    float TSF(close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    一种历史资料延伸预测，也称历史引伸预测法。是以时间数列所能反映的社会经济现象的发展过程和规律性，进行引伸外推，预测其发展趋势的方法',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'VAR(close, timeperiod=5, nbdev=1)',
                insertText      : 'VAR(${1})',
                detail          : '# 方差\n' +
                                  '    float VAR(close, timeperiod=5, nbdev=1)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    方差用来计算每一个变量（观察值）与总体均数之间的差异。为避免出现离均差总和为零，离均差平方和受样本含量的影响，统计学采用平均离均差平方和来描述变量的变异程',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ATR(high, low, close, timeperiod=14)',
                insertText      : 'ATR(${1})',
                detail          : '# 真实波动幅度均值\n' +
                                  '    float ATR(high, low, close, timeperiod=14)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    真实波动幅度均值（ATR)是以 N 天的指数移动平均数平均後的交易波动幅度。 \n' +
                                  '\n' +
                                  '公式：\n' +
                                  '    一天的交易幅度只是单纯地 最大值 - 最小值。\n' +
                                  '    而真实波动幅度则包含昨天的收盘价，若其在今天的幅度之外：\n' +
                                  '    真实波动幅度 = max(最大值,昨日收盘价) − min(最小值,昨日收盘价) 真实波动幅度均值便是「真实波动幅度」的 N 日 指数移动平均数。\n' +
                                  '\n' + 
                                  '特性：\n' +
                                  '    波动幅度的概念表示可以显示出交易者的期望和热情。\n' +
                                  '    大幅的或增加中的波动幅度表示交易者在当天可能准备持续买进或卖出股票。\n' +
                                  '    波动幅度的减少则表示交易者对股市没有太大的兴趣。',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'NATR(high, low, close, timeperiod=14)',
                insertText      : 'NATR(${1})',
                detail          : '# 归一化波动幅度均值\n' +
                                  '    float NATR(high, low, close, timeperiod=14)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'TRANGE(high, low, close)',
                insertText      : 'TRANGE(${1})',
                detail          : '# 真正的范围\n' +
                                  '    float TRANGE(high, low, close)',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'AD(high, low, close, volume)',
                insertText      : 'AD(${1})',
                detail          : '# 累积/派发线\n' +
                                  '    float AD(high, low, close, volume)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    Marc Chaikin提出的一种平衡交易量指标，以当日的收盘价位来估算成交流量，用于估定一段时间内该证券累积的资金流量。\n' +
                                  '\n' +
                                  '公式：\n' +
                                  '    A/D = 昨日A/D + 多空对比 * 今日成交量\n' +
                                  '    多空对比 = [（收盘价- 最低价） - （最高价 - 收盘价）] / （最高价 - 最低价)\n' +
                                  '    若最高价等于最低价： 多空对比 = （收盘价 / 昨收盘） - 1\n' +
                                  '\n' + 
                                  '研判：\n' +
                                  '    1. A/D测量资金流向，向上的A/D表明买方占优势，而向下的A/D表明卖方占优势\n' +
                                  '    2. A/D与价格的背离可视为买卖信号，即底背离考虑买入，顶背离考虑卖出\n' +
                                  '    3. 应当注意A/D忽略了缺口的影响，事实上，跳空缺口的意义是不能轻易忽略的\n' +
                                  '    4. A/D指标无需设置参数，但在应用时，可结合指标的均线进行分析',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)',
                insertText      : 'ADOSC(${1})',
                detail          : '# 震荡指标\n' +
                                  '    float ADOSC(high, low, close, volume, fastperiod=3, slowperiod=10)\n' +
                                  '\n' +
                                  '简介：\n' +
                                  '    将资金流动情况与价格行为相对比，检测市场中资金流入和流出的情况。\n' +
                                  '\n' +
                                  '公式：\n' +
                                  '    fastperiod A/D - slowperiod A/D\n' +
                                  '\n' + 
                                  '研判：\n' +
                                  '    1. 交易信号是背离：看涨背离做多，看跌背离做空\n' +
                                  '    2. 股价与90天移动平均结合，与其他指标结合\n' +
                                  '    3. 由正变负卖出，由负变正买进',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            },{
                label           : 'OBV(close, volume)',
                insertText      : 'OBV(${1})',
                detail          : '# 能量潮\n' +
                                  '    float OBV(close, volume)\n' +
                                  '简介：\n' +
                                  '    Joe Granville提出，通过统计成交量变动的趋势推测股价趋势。\n' +
                                  '\n' +
                                  '公式：\n' +
                                  '    以某日为基期，逐日累计每日上市股票总成交量，若隔日指数或股票上涨，则基期OBV加上本日成交量为本日OBV。隔日指数或股票下跌，则基期OBV减去本日成交量为本日OBV\n' +  
                                  '    多空比率净额 = [（收盘价－最低价）－（最高价-收盘价）] ÷（ 最高价－最低价）×成交量\n' +
                                  '\n' + 
                                  '研判：\n' +
                                  '    1. 以“N”字型为波动单位，一浪高于一浪称“上升潮”，下跌称“跌潮”；上升潮买进，跌潮卖出\n' +
                                  '    2. 须配合K线图走势\n' +
                                  '    3. 用多空比率净额法进行修正，但不知TA-Lib采用哪种方法',
                kind            : monaco.languages.CompletionItemKind.Function,
                insertTextRules : monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet
            }
        ]
    };

    init_provide_hover();
}

// 初始化provide_hover字典
function init_provide_hover(){
    if (provide_hover.length >0)
        return;

    for (i in function_info){
        var node = function_info[i];
        for (j in node){
            val = node[j];
            if (!val.detail)
                continue;

            var str = val.insertText.match(/[@a-z_A-Z]*\w*/);
            provide_hover[str] = val.detail;
        }
    }
}
