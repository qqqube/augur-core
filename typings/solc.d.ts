declare module 'solc' {
    interface CompilerInputSourceFile {
        keccak256?: string;
<<<<<<< HEAD
        content: string;
=======
        urls: string[];
>>>>>>> cc859ecf6964c8f529f829a4463db2d742e1d6a4
    }
    interface CompilerInputSourceCode {
        keccak256?: string;
        content: string;
    }
    interface CompilerInput {
        language: "Solidity" | "serpent" | "lll" | "assembly";
        sources: {
            [globalName: string]: CompilerInputSourceFile,
        };
    }
    type ReadCallback = (path: string) => { contents?: string, error?: string};
    function compileStandardWrapper(input: string, readCallback?: ReadCallback);
}
