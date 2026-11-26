package com.sandy.pit;

import org.pitest.bytecode.ASMVersion;
import org.pitest.mutationtest.engine.MutationIdentifier;
import org.pitest.mutationtest.engine.gregor.MethodInfo;
import org.pitest.mutationtest.engine.gregor.MethodMutatorFactory;
import org.pitest.mutationtest.engine.gregor.MutationContext;
import org.pitest.reloc.asm.Label;
import org.pitest.reloc.asm.MethodVisitor;
import org.pitest.reloc.asm.Opcodes;

/**
 * BR2 custom mutator: removes the department equality check in {@code ExpenseService.assertCanDecide}
 * so that managers appear allowed to approve or reject requests from any department.
 */
public class DropDepartmentCheckMutator implements MethodMutatorFactory {

    @Override
    public MethodVisitor create(MutationContext context, MethodInfo methodInfo, MethodVisitor methodVisitor) {
        if (!"assertCanDecide".equals(methodInfo.getName())) {
            return methodVisitor;
        }
        return new MethodVisitor(ASMVersion.ASM_VERSION, methodVisitor) {
            private boolean sawGetDepartmentId;
            private boolean sawLongEqualsAfterDept;

            @Override
            public void visitMethodInsn(int opcode, String owner, String name, String descriptor, boolean isInterface) {
                if (opcode == Opcodes.INVOKEVIRTUAL
                        && "com/sandy/expense/security/AppUserPrincipal".equals(owner)
                        && "getDepartmentId".equals(name)) {
                    sawGetDepartmentId = true;
                } else if (sawGetDepartmentId
                        && opcode == Opcodes.INVOKEVIRTUAL
                        && "java/lang/Long".equals(owner)
                        && "equals".equals(name)) {
                    sawLongEqualsAfterDept = true;
                } else {
                    sawGetDepartmentId = false;
                    sawLongEqualsAfterDept = false;
                }
                super.visitMethodInsn(opcode, owner, name, descriptor, isInterface);
            }

            @Override
            public void visitJumpInsn(int opcode, Label label) {
                if (sawLongEqualsAfterDept && opcode == Opcodes.IFNE) {
                    sawGetDepartmentId = false;
                    sawLongEqualsAfterDept = false;
                    MutationIdentifier id = context.registerMutation(
                            DropDepartmentCheckMutator.this,
                            "BR2 custom mutator: dropped department check in assertCanDecide");
                    if (context.shouldMutate(id)) {
                        // Pop the boolean result of Long.equals off the stack and jump past the throw
                        mv.visitInsn(Opcodes.POP);
                        mv.visitJumpInsn(Opcodes.GOTO, label);
                        return;
                    }
                } else {
                    sawGetDepartmentId = false;
                    sawLongEqualsAfterDept = false;
                }
                super.visitJumpInsn(opcode, label);
            }
        };
    }

    @Override
    public String getGloballyUniqueId() {
        return getClass().getName();
    }

    @Override
    public String getName() {
        return "DROP_DEPARTMENT_CHECK";
    }
}
