"""
P3.3 Cloud & Deployment Tools

Infrastructure and DevOps operations.
"""

from typing import Any, Dict, List, Optional
import asyncio


class DeployResult:
    """Result of a deployment operation."""
    def __init__(self, success: bool, resource_id: str, url: str, message: str):
        self.success = success
        self.resource_id = resource_id
        self.url = url
        self.message = message


class BuildResult:
    """Result of a build operation."""
    def __init__(self, success: bool, image_id: str, tags: List[str], message: str):
        self.success = success
        self.image_id = image_id
        self.tags = tags
        self.message = message


class ContainerResult:
    """Result of a container operation."""
    def __init__(self, success: bool, container_id: str, message: str):
        self.success = success
        self.container_id = container_id
        self.message = message


class PlanResult:
    """Result of infrastructure planning."""
    def __init__(self, success: bool, changes: Dict[str, int], plan_output: str):
        self.success = success
        self.changes = changes  # {"add": 0, "change": 0, "destroy": 0}
        self.plan_output = plan_output


class ApplyResult:
    """Result of infrastructure apply."""
    def __init__(self, success: bool, resources: List[str], message: str):
        self.success = success
        self.resources = resources
        self.message = message


class CloudDeploymentTools:
    """Cloud deployment and infrastructure tools."""

    def __init__(self):
        self._docker_available = False
        self._check_docker()

    def _check_docker(self) -> None:
        """Check if Docker is available."""
        import shutil
        self._docker_available = shutil.which("docker") is not None

    async def aws_deploy_lambda(
        self,
        function_name: str,
        code_path: str,
        config: Dict[str, Any]
    ) -> DeployResult:
        """
        Deploy AWS Lambda function.

        Note: Requires AWS CLI and credentials configured.
        """
        try:
            # Create deployment package
            handler = config.get("handler", "lambda_function.lambda_handler")
            runtime = config.get("runtime", "python3.9")
            role = config.get("role", "")
            memory = config.get("memory", 128)
            timeout = config.get("timeout", 30)

            # Zip the code
            zip_cmd = f"zip -r /tmp/{function_name}.zip {code_path}"
            process = await asyncio.create_subprocess_shell(
                zip_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            # Deploy using AWS CLI
            cmd = f"""aws lambda create-function \
                --function-name {function_name} \
                --runtime {runtime} \
                --role {role} \
                --handler {handler} \
                --zip-file fileb:///tmp/{function_name}.zip \
                --memory-size {memory} \
                --timeout {timeout}"""

            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return DeployResult(
                    success=True,
                    resource_id=function_name,
                    url=f"arn:aws:lambda:region:account:function:{function_name}",
                    message="Lambda function deployed successfully"
                )
            else:
                return DeployResult(
                    success=False,
                    resource_id="",
                    url="",
                    message=stderr.decode()
                )

        except Exception as e:
            return DeployResult(
                success=False,
                resource_id="",
                url="",
                message=str(e)
            )

    async def docker_build(
        self,
        dockerfile: str,
        tag: str,
        context: str = "."
    ) -> BuildResult:
        """
        Build a Docker image.

        Args:
            dockerfile: Path to Dockerfile
            tag: Image tag
            context: Build context directory
        """
        if not self._docker_available:
            return BuildResult(
                success=False,
                image_id="",
                tags=[],
                message="Docker is not available"
            )

        cmd = f"docker build -f {dockerfile} -t {tag} {context}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            # Get image ID
            id_cmd = f"docker images -q {tag}"
            id_process = await asyncio.create_subprocess_shell(
                id_cmd,
                stdout=asyncio.subprocess.PIPE
            )
            id_out, _ = await id_process.communicate()

            return BuildResult(
                success=True,
                image_id=id_out.decode().strip(),
                tags=[tag],
                message="Image built successfully"
            )
        else:
            return BuildResult(
                success=False,
                image_id="",
                tags=[],
                message=stderr.decode()
            )

    async def docker_push(
        self,
        image: str,
        registry: str
    ) -> DeployResult:
        """
        Push Docker image to registry.

        Args:
            image: Image name/tag
            registry: Registry URL
        """
        if not self._docker_available:
            return DeployResult(
                success=False,
                resource_id="",
                url="",
                message="Docker is not available"
            )

        full_tag = f"{registry}/{image}"

        # Tag for registry
        tag_cmd = f"docker tag {image} {full_tag}"
        await asyncio.create_subprocess_shell(tag_cmd)

        # Push
        cmd = f"docker push {full_tag}"
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        return DeployResult(
            success=process.returncode == 0,
            resource_id=full_tag,
            url=f"https://{registry}/{image}",
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def docker_run(
        self,
        image: str,
        command: Optional[str] = None,
        ports: Optional[Dict[str, str]] = None,
        detach: bool = True
    ) -> ContainerResult:
        """
        Run a Docker container.

        Args:
            image: Image to run
            command: Optional command to run
            ports: Port mappings {"host": "container"}
            detach: Run in background
        """
        if not self._docker_available:
            return ContainerResult(
                success=False,
                container_id="",
                message="Docker is not available"
            )

        cmd = "docker run"

        if detach:
            cmd += " -d"

        if ports:
            for host_port, container_port in ports.items():
                cmd += f" -p {host_port}:{container_port}"

        cmd += f" {image}"

        if command:
            cmd += f" {command}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        return ContainerResult(
            success=process.returncode == 0,
            container_id=stdout.decode().strip() if process.returncode == 0 else "",
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def k8s_apply(self, manifest: str) -> ApplyResult:
        """
        Apply Kubernetes manifest.

        Args:
            manifest: Path to manifest file or directory
        """
        cmd = f"kubectl apply -f {manifest}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        resources = []
        for line in stdout.decode().splitlines():
            if " created" in line or " configured" in line:
                resources.append(line.split()[0])

        return ApplyResult(
            success=process.returncode == 0,
            resources=resources,
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )

    async def terraform_plan(self, config_dir: str) -> PlanResult:
        """
        Plan Terraform infrastructure changes.

        Args:
            config_dir: Directory with Terraform config
        """
        # Init first
        init_cmd = f"terraform -chdir={config_dir} init"
        await asyncio.create_subprocess_shell(init_cmd)

        # Plan
        cmd = f"terraform -chdir={config_dir} plan -no-color"
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # Parse changes from output
        output = stdout.decode()
        changes = {"add": 0, "change": 0, "destroy": 0}

        if "to add" in output:
            import re
            match = re.search(r'(\d+) to add', output)
            if match:
                changes["add"] = int(match.group(1))

        return PlanResult(
            success=process.returncode == 0,
            changes=changes,
            plan_output=output if process.returncode == 0 else stderr.decode()
        )

    async def terraform_apply(
        self,
        config_dir: str,
        auto_approve: bool = False
    ) -> ApplyResult:
        """
        Apply Terraform infrastructure.

        Args:
            config_dir: Directory with Terraform config
            auto_approve: Skip confirmation
        """
        cmd = f"terraform -chdir={config_dir} apply -no-color"
        if auto_approve:
            cmd += " -auto-approve"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        return ApplyResult(
            success=process.returncode == 0,
            resources=[],
            message=stdout.decode() if process.returncode == 0 else stderr.decode()
        )
