// Inspect original Japanese item arithmetic and its callers locally.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryBlock;

public class CrystalHeldCapProbe extends GhidraScript {
    public void run() throws Exception {
        if (!currentProgram.getName().contains("Japan")) return;
        MemoryBlock block=currentProgram.getMemory().getBlock("rom13");
        if (block==null) throw new IllegalStateException("Missing bank 13");
        println("HELD_CAP_ORIGINAL " + currentProgram.getName());
        for (int offset : new int[]{0x52cb,0x52d8,0x53e9,0x53f1}) {
            Address address=block.getStart().add(offset-0x4000);
            disassemble(address);
            for (int i=0;i<8;i++) {
                Instruction instruction=currentProgram.getListing().getInstructionAt(address);
                if (instruction==null) break;
                println("HELD_CAP " + address + " " + instruction);
                address=address.add(instruction.getLength());
            }
        }
    }
}
