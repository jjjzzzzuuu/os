package daemon

import (
	"fmt"

	"github.com/Sirupsen/logrus"
)

// ContainerRename changes the name of a container, using the oldName
// to find the container. An error is returned if newName is already
// reserved.
func (daemon *Daemon) ContainerRename(oldName, newName string) error {
	if oldName == "" || newName == "" {
		return fmt.Errorf("Neither old nor new names may be empty")
	}

	container, err := daemon.GetContainer(oldName)
	if err != nil {
		return err
	}

	oldName = container.Name

	container.Lock()
	defer container.Unlock()
	if newName, err = daemon.reserveName(container.ID, newName); err != nil {
		return fmt.Errorf("Error when allocating new name: %v", err)
	}

	container.Name = newName

	defer func() {
		if err != nil {
			container.Name = oldName
			daemon.reserveName(container.ID, oldName)
			daemon.releaseName(newName)
		}
	}()

	daemon.releaseName(oldName)
	if err = container.ToDisk(); err != nil {
		return err
	}

	attributes := map[string]string{
		"oldName": oldName,
	}

	if !container.Running {
		daemon.LogContainerEventWithAttributes(container, "rename", attributes)
		return nil
	}

	defer func() {
		if err != nil {
			container.Name = oldName
			if e := container.ToDisk(); e != nil {
				logrus.Errorf("%s: Failed in writing to Disk on rename failure: %v", container.ID, e)
			}
		}
	}()

	daemon.LogContainerEventWithAttributes(container, "rename", attributes)
	return nil
}
