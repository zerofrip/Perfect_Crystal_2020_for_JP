// Local Ghidra code/data mapping for the Japanese Crystal port.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.mem.MemoryBlock;

public class CrystalTargetProbe extends GhidraScript {
    @Override
    public void run() throws Exception {
        println("PROGRAM " + currentProgram.getName());
        for (int bank : new int[] {5, 11, 15, 32, 62}) {
            MemoryBlock block = currentProgram.getMemory().getBlock("rom" + bank);
            if (block == null) {
                println("MISSING_BANK " + bank);
                continue;
            }
            println("BANK " + bank + " " + block.getStart() + " " + block.getEnd());
        }
        for (int[] target : new int[][] {
            {11, 0x5A2B}, {11, 0x5C37}, {32, 0x418D},
            {15, 0x6D57}, {62, 0x7F93}
        }) {
            MemoryBlock block = currentProgram.getMemory().getBlock("rom" + target[0]);
            if (block == null) continue;
            Address address = block.getStart().add(target[1] - 0x4000);
            Instruction instruction = currentProgram.getListing().getInstructionAt(address);
            if (instruction == null) {
                disassemble(address);
                instruction = currentProgram.getListing().getInstructionAt(address);
            }
            println("TARGET " + target[0] + " " + address + " " +
                (instruction == null ? "no instruction" : instruction.toString()));
        }
    }
}
