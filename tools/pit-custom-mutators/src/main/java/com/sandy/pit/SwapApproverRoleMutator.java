package com.sandy.pit;

import org.pitest.bytecode.ASMVersion;
import org.pitest.mutationtest.engine.MutationIdentifier;
import org.pitest.mutationtest.engine.gregor.MethodInfo;
import org.pitest.mutationtest.engine.gregor.MethodMutatorFactory;
import org.pitest.mutationtest.engine.gregor.MutationContext;
import org.pitest.reloc.asm.MethodVisitor;
import org.pitest.reloc.asm.Opcodes;

/**
 * BR3/BR4 custom mutator: swaps {@code Role.MANAGER} and {@code Role.FINANCE} ownership inside
 * {@code RequestStatus.approverRole()}, reversing which role controls SUBMITTED vs MANAGER_APPROVED.
 */
public class SwapApproverRoleMutator implements MethodMutatorFactory {

    private static final String ROLE_OWNER = "com/sandy/expense/domain/Role";
    private static final String ROLE_DESC = "Lcom/sandy/expense/domain/Role;";

    @Override
    public MethodVisitor create(MutationContext context, MethodInfo methodInfo, MethodVisitor methodVisitor) {
        if (!"approverRole".equals(methodInfo.getName())) {
            return methodVisitor;
        }
        return new MethodVisitor(ASMVersion.ASM_VERSION, methodVisitor) {
            @Override
            public void visitFieldInsn(int opcode, String owner, String name, String descriptor) {
                if (opcode == Opcodes.GETSTATIC && ROLE_OWNER.equals(owner) && ROLE_DESC.equals(descriptor)) {
                    if ("MANAGER".equals(name)) {
                        MutationIdentifier id = context.registerMutation(
                                SwapApproverRoleMutator.this,
                                "BR3/BR4 custom mutator: swapped Role.MANAGER to Role.FINANCE in approverRole");
                        if (context.shouldMutate(id)) {
                            super.visitFieldInsn(opcode, owner, "FINANCE", descriptor);
                            return;
                        }
                    } else if ("FINANCE".equals(name)) {
                        MutationIdentifier id = context.registerMutation(
                                SwapApproverRoleMutator.this,
                                "BR3/BR4 custom mutator: swapped Role.FINANCE to Role.MANAGER in approverRole");
                        if (context.shouldMutate(id)) {
                            super.visitFieldInsn(opcode, owner, "MANAGER", descriptor);
                            return;
                        }
                    }
                }
                super.visitFieldInsn(opcode, owner, name, descriptor);
            }
        };
    }

    @Override
    public String getGloballyUniqueId() {
        return getClass().getName();
    }

    @Override
    public String getName() {
        return "SWAP_APPROVER_ROLE";
    }
}
