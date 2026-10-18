// Local Ghidra inspection script. Outputs metadata only, never ROM bytes.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.mem.MemoryBlock;

public class CrystalProbe extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("PROGRAM " + currentProgram.getName());
        println("LANGUAGE " + currentProgram.getLanguageID());
        MemoryBlock[] blocks = currentProgram.getMemory().getBlocks();
        println("BLOCK_COUNT " + blocks.length);
        for (int i = 0; i < Math.min(blocks.length, 8); i++) {
            println("BLOCK " + blocks[i].getName() + " " + blocks[i].getStart()
                + " " + blocks[i].getEnd());
        }
        FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
        int count = 0;
        while (it.hasNext()) {
            Function fn = it.next();
            if (count < 20) {
                println("FUNCTION " + fn.getEntryPoint() + " " + fn.getName());
            }
            count++;
        }
        println("FUNCTION_COUNT " + count);
    }
}
