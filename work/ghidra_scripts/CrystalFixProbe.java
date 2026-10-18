// Confirm the original Japanese routines for the four requested RC2 fixes.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryBlock;

public class CrystalFixProbe extends GhidraScript {
    public void run() throws Exception {
        if (!currentProgram.getName().contains("Japan")) return;
        println("RC2_FIX_BASE " + currentProgram.getName());
        for (int[] target : new int[][] {
            {3,0x6f52},{13,0x6305},{0x3e,0x7df5},{13,0x7e03},{13,0x5612}
        }) {
            MemoryBlock block=currentProgram.getMemory().getBlock("rom"+target[0]);
            if (block==null) throw new IllegalStateException("Missing bank " + target[0]);
            Address address=block.getStart().add(target[1]-0x4000);
            disassemble(address);
            Instruction instruction=currentProgram.getListing().getInstructionAt(address);
            if (instruction==null) throw new IllegalStateException("Missing instruction " + address);
            println("RC2_FIX_TARGET " + target[0] + " " + address + " " + instruction);
        }
    }
}
