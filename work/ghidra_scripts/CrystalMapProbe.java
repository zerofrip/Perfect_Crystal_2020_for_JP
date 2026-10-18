// Verify actual Japanese map/script routines; never export ROM contents.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryBlock;

public class CrystalMapProbe extends GhidraScript {
    public void run() throws Exception {
        println("PROGRAM " + currentProgram.getName());
        if (!currentProgram.getName().contains("Japan")) return;
        for (int[] target : new int[][] {
            {0,0x2be1},{0,0x2c12},{0,0x2697},{0x25,0x6ca9},
            {0x24,0x652a},{0x24,0x6539}
        }) {
            Address address;
            if (target[0] == 0) {
                address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(target[1]);
            } else {
                MemoryBlock block = currentProgram.getMemory().getBlock("rom"+target[0]);
                if (block == null) { println("MISSING_BANK " + target[0]); continue; }
                address = block.getStart().add(target[1]-0x4000);
            }
            disassemble(address);
            Instruction instruction = currentProgram.getListing().getInstructionAt(address);
            println("MAP_TARGET " + target[0] + " " + address + " " + instruction);
        }
    }
}
